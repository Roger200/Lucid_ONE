# Lucid_ONE
Desktop and portable 7-axis robotic arm by AMBER Robotics

### API of UDP Protocol, check https://github.com/MrAsana/UDP-Protocol-API

### Robotic arm control Api
https://github.com/MrAsana/Robotic_arm_api

## Gazebo Pick and Place Simulation

This section describes how to set up and run the Gazebo pick and place simulation for the Amber L1 robot.

### Prerequisites

*   ROS 2 (Humble Hawksbill recommended). Ensure your ROS 2 environment is sourced.
*   Gazebo (comes with ROS 2 Desktop Full install).
*   `colcon` (ROS 2 build tool).
*   Git (to clone this repository).
*   Any dependencies required by the packages (though most are standard ROS 2 packages).

### Building the Workspace

1.  **Clone the Repository:**
    If you haven't already, clone this repository into your ROS 2 workspace's `src` directory:
    ```bash
    cd ~/your_ros2_ws/src
    git clone <repository_url> . 
    # Or if you are already in the cloned repo, ensure you are in the workspace src directory
    ```

2.  **Install Dependencies (if any new ones were added beyond standard ROS/Gazebo):**
    From the root of your workspace (`~/your_ros2_ws`), run:
    ```bash
    rosdep install --from-paths src --ignore-src -r -y
    ```

3.  **Build the Workspace:**
    Navigate to the root of your workspace and build using `colcon`:
    ```bash
    cd ~/your_ros2_ws
    colcon build --symlink-install
    ```
    *Note: `--symlink-install` is recommended for development as it allows you to change Python scripts or launch files without rebuilding, but a clean build without it might be needed if you encounter issues.*


### Running the Simulation

1.  **Source the Workspace:**
    After a successful build, source your workspace's setup files in every new terminal you use for this project:
    ```bash
    cd ~/your_ros2_ws
    source install/setup.bash
    ```

2.  **Launch the Gazebo Simulation Environment:**
    This will start Gazebo, load the world, spawn the Amber L1 robot, and start the necessary controllers.
    ```bash
    ros2 launch amber_l1_description amber_l1_gazebo.launch.py
    ```
    Wait for Gazebo to fully load and for the robot to appear. You should see messages indicating that controllers have been loaded and started.

3.  **Run the Pick and Place Script:**
    In a **new terminal** (after sourcing the workspace again), launch the pick and place script:
    ```bash
    ros2 launch amber_l1_pick_place pick_place.launch.py
    ```
    The robot should then execute the pre-programmed pick and place sequence in Gazebo.

### Tuning and Iteration
The pre-defined joint positions and gripper efforts in `amber_l1_pick_place/pick_place_script.py` are initial estimates. You will likely need to:
*   Adjust these joint positions to accurately reach and grasp the cube.
*   Tune gripper effort values for successful grasping.
*   Modify timing and delays in the script for smoother operation.

Edit the script, then re-launch the `pick_place.launch.py` to see your changes. You typically do not need to rebuild the workspace for Python script changes if you used `--symlink-install`.
