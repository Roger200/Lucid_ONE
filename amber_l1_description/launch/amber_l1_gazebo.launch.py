import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution, TextSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock if true",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "world",
            default_value=PathJoinSubstitution(
                [
                    FindPackageShare("amber_l1_description"),
                    "worlds",
                    "pick_place.world",
                ]
            ),
            description="SDF world file to load.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui", default_value="true", description="Enable Gazebo GUI"
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "server", default_value="true", description="Enable Gazebo server"
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "debug", default_value="false", description="Enable Gazebo debug mode"
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "prefix",
            default_value="",
            description="Prefix for the robot name in Gazebo.",
        )
    )

    # Initialize Arguments
    use_sim_time = LaunchConfiguration("use_sim_time")
    world = LaunchConfiguration("world")
    gui = LaunchConfiguration("gui")
    server = LaunchConfiguration("server")
    debug = LaunchConfiguration("debug")
    prefix = LaunchConfiguration("prefix")

    # Get URDF path
    urdf_file_path = PathJoinSubstitution(
        [FindPackageShare("amber_l1_description"), "urdf", "amber_l1.urdf.xacro"]
    )

    # Process URDF
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        urdf_file_path,
        " ",
        "is_hw:='false'", # Crucial for simulation
        " ",
        "prefix:=",
        prefix,
    ])
    robot_description = {"robot_description": robot_description_content}

    # Gazebo launch
    gazebo_launch_file = PathJoinSubstitution(
        [get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py']
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_file),
        launch_arguments={
            'world': world,
            'gui': gui,
            'server': server,
            'debug': debug,
            'verbose': 'false', # Add other Gazebo args as needed
            'pause': 'false',
        }.items(),
    )

    # Robot State Publisher Node
    # Note: parameters use a dictionary format now, not a list of tuples for robot_description
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    # Spawn Entity Node
    spawn_entity_node = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", TextSubstitution(text="amber_l1"), "-robot_namespace", prefix],
        output="screen",
    )

    # Joint State Broadcaster Spawner
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Joint Trajectory Controller Spawner (Arm)
    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["amber_l1_arm_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )
    
    # Gripper Controller Spawner
    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["amber_l1_gripper_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Build the launch description
    ld = LaunchDescription()

    # Add declared arguments
    for arg in declared_arguments:
        ld.add_action(arg)

    # Add actions
    ld.add_action(gazebo)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(spawn_entity_node)
    # Adding spawners directly. If issues arise with controllers not starting,
    # event handlers (e.g., OnProcessExit of spawn_entity_node) might be needed.
    ld.add_action(joint_state_broadcaster_spawner)
    ld.add_action(arm_controller_spawner)
    ld.add_action(gripper_controller_spawner)
    
    return ld
