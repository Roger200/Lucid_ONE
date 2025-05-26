from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='amber_l1_pick_place',
            executable='pick_place_script', # Name defined in setup.py entry_points
            name='amber_l1_pick_place_node', # This will be the node name used in logs
            output='screen',
            emulate_tty=True, # Useful for seeing print statements from the script
        )
    ])
