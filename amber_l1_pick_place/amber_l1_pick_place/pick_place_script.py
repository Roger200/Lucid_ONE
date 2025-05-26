import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from std_msgs.msg import Float64MultiArray
from builtin_interfaces.msg import Duration
import time

class PickPlaceNode(Node):
    def __init__(self):
        super().__init__('amber_l1_pick_place_node')
        self.get_logger().info('Pick and Place Node started.')

        # Joint Definitions
        self.arm_joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7']
        self.gripper_joint_names = ['gripper_finger_left_joint', 'gripper_finger_right_joint']

        # Pre-defined Joint Configurations (example values, might need tuning)
        self.HOME_POSITION = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.APPROACH_CUBE_POSITION = [0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0]
        self.PICK_CUBE_POSITION = [0.0, -0.2, 0.0, 1.2, 0.0, 0.2, 0.0]
        self.LIFT_CUBE_POSITION = [0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0] # Same as approach for now
        self.PLACE_APPROACH_POSITION = [1.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0]
        self.PLACE_POSITION = [1.0, -0.2, 0.0, 1.2, 0.0, 0.2, 0.0]

        # Action Client for arm controller
        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/amber_l1_arm_controller/follow_joint_trajectory'
        )
        self.get_logger().info('Waiting for arm action server...')
        self._action_client.wait_for_server()
        self.get_logger().info('Arm action server found.')

        # Publisher for gripper controller
        self.gripper_publisher = self.create_publisher(
            Float64MultiArray,
            '/amber_l1_gripper_controller/commands',
            10
        )
        self.get_logger().info('Waiting for gripper publisher to be ready...')
        # Wait for publisher to be ready (e.g. by checking subscriber count or a short delay)
        # For simplicity, a small delay is used here. In a robust system, check subscriber count.
        time.sleep(1.0) 
        self.get_logger().info('Gripper publisher ready.')


    def send_arm_goal(self, joint_positions, duration_sec=5.0):
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.arm_joint_names
        
        point = JointTrajectoryPoint()
        point.positions = joint_positions
        point.time_from_start = Duration(sec=int(duration_sec), nanosec=int((duration_sec % 1) * 1e9))
        goal_msg.trajectory.points.append(point)

        self.get_logger().info(f"Sending arm goal: {joint_positions} over {duration_sec}s")
        
        # Store the future to check for completion
        self.send_goal_future = self._action_client.send_goal_async(goal_msg)
        
        # Wait for the goal to be accepted
        rclpy.spin_until_future_complete(self, self.send_goal_future)
        goal_handle = self.send_goal_future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Arm goal rejected :(')
            return False

        self.get_logger().info('Arm goal accepted :)')
        
        # Wait for the result
        self.get_result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, self.get_result_future)
        result = self.get_result_future.result().result

        if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL:
            self.get_logger().info('Arm trajectory successful!')
            return True
        else:
            self.get_logger().error(f'Arm trajectory failed with error code: {result.error_code}')
            return False

    def operate_gripper(self, efforts, delay_sec=1.0):
        msg = Float64MultiArray()
        msg.data = [float(e) for e in efforts] # Ensure data is float
        self.get_logger().info(f"Operating gripper with efforts: {efforts}")
        self.gripper_publisher.publish(msg)
        time.sleep(delay_sec) # Give time for the command to take effect

    def run_pick_place_sequence(self):
        self.get_logger().info("Starting pick and place sequence...")

        # 1. Go to HOME_POSITION
        self.get_logger().info("Going to HOME position.")
        if not self.send_arm_goal(self.HOME_POSITION, duration_sec=5.0):
            self.get_logger().error("Failed to reach HOME position. Aborting.")
            return

        # 2. Open gripper
        self.get_logger().info("Opening gripper.")
        self.operate_gripper([0.0, 0.0], delay_sec=2.0) # Example: 0.0 effort to open

        # 3. Go to APPROACH_CUBE_POSITION
        self.get_logger().info("Going to APPROACH_CUBE position.")
        if not self.send_arm_goal(self.APPROACH_CUBE_POSITION, duration_sec=5.0):
            self.get_logger().error("Failed to reach APPROACH_CUBE position. Aborting.")
            return

        # 4. Go to PICK_CUBE_POSITION
        self.get_logger().info("Going to PICK_CUBE position.")
        if not self.send_arm_goal(self.PICK_CUBE_POSITION, duration_sec=3.0):
            self.get_logger().error("Failed to reach PICK_CUBE position. Aborting.")
            return

        # 5. Close gripper
        self.get_logger().info("Closing gripper.")
        self.operate_gripper([0.8, 0.8], delay_sec=2.0) # Example: 0.8 effort to close (tune this)

        # 6. Go to LIFT_CUBE_POSITION
        self.get_logger().info("Going to LIFT_CUBE position.")
        if not self.send_arm_goal(self.LIFT_CUBE_POSITION, duration_sec=3.0):
            self.get_logger().error("Failed to reach LIFT_CUBE position. Aborting.")
            return
            
        # 7. Go to PLACE_APPROACH_POSITION
        self.get_logger().info("Going to PLACE_APPROACH position.")
        if not self.send_arm_goal(self.PLACE_APPROACH_POSITION, duration_sec=6.0):
            self.get_logger().error("Failed to reach PLACE_APPROACH position. Aborting.")
            return

        # 8. Go to PLACE_POSITION
        self.get_logger().info("Going to PLACE position.")
        if not self.send_arm_goal(self.PLACE_POSITION, duration_sec=3.0):
            self.get_logger().error("Failed to reach PLACE position. Aborting.")
            return

        # 9. Open gripper
        self.get_logger().info("Opening gripper.")
        self.operate_gripper([0.0, 0.0], delay_sec=2.0)

        # 10. Go to HOME_POSITION
        self.get_logger().info("Going to HOME position.")
        if not self.send_arm_goal(self.HOME_POSITION, duration_sec=6.0):
            self.get_logger().error("Failed to reach HOME position after placing.")
            # Not aborting here, as the main task is done.
            
        self.get_logger().info("Pick and place sequence completed.")

def main(args=None):
    rclpy.init(args=args)
    pick_place_node = None
    try:
        pick_place_node = PickPlaceNode()
        pick_place_node.run_pick_place_sequence()
    except Exception as e:
        if pick_place_node:
            pick_place_node.get_logger().error(f"Unhandled exception: {e}")
        else:
            print(f"Unhandled exception during node initialization: {e}")
    finally:
        if pick_place_node:
            pick_place_node.destroy_node()
        rclpy.shutdown()
        if pick_place_node:
             pick_place_node.get_logger().info("Node shutdown complete.")

if __name__ == '__main__':
    main()
