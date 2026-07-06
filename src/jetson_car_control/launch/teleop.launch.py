from launch import LaunchDescription # top-level container for all launch actions
from launch.actions import EmitEvent, RegisterEventHandler # event-driven lifecycle transitions
from launch.event_handlers import OnProcessStart # trigger when node process starts
from launch.events import matches_action # match events to specific node actions
from launch_ros.actions import LifecycleNode # ROS 2 lifecycle-aware node launcher
from launch_ros.event_handlers import OnStateTransition # trigger on lifecycle state change
from launch_ros.events.lifecycle import ChangeState # request a lifecycle state transition
from lifecycle_msgs.msg import Transition # transition ID constants


def generate_launch_description(): # required entry point; launch system calls this function
    # Keyboard teleop reads stdin. ros2 launch does not forward keystrokes from this
    # terminal to child processes (emulate_tty only affects stdout coloring).
    # prefix='xterm -e' opens the node in its own terminal with a real TTY for keys.
    # Requires: sudo apt install xterm
    # Alternative without xterm: ros2 run jetson_car_control teleop_lifecycle
    #   then ros2 lifecycle set /teleop_lifecycle configure && ... activate
    teleop_node = LifecycleNode( # declare the lifecycle node to launch
        package='jetson_car_control', # ROS package containing the executable
        executable='teleop_lifecycle', # binary name from CMakeLists.txt add_executable
        name='teleop_lifecycle', # node name in the ROS graph (used by ros2 lifecycle get)
        namespace='',
        output='screen', # print node logs to launch terminal
        prefix='xterm -e', # separate TTY so keyboard input reaches the node
    )

    configure_handler = RegisterEventHandler( # register an event-driven callback
        OnProcessStart( # fire when the node process has started
            target_action=teleop_node, # watch this specific node
            on_start=[ # actions to run when process starts
                EmitEvent( # emit a lifecycle change event
                    event=ChangeState( # request state transition
                        lifecycle_node_matcher=matches_action(teleop_node), # target this node
                        transition_id=Transition.TRANSITION_CONFIGURE, # configure: unconfigured → inactive
                    )
                ),
            ],
        )
    )

    activate_handler = RegisterEventHandler( # second event handler for activation
        OnStateTransition( # fire when lifecycle state changes
            target_lifecycle_node=teleop_node, # watch this node
            goal_state='inactive', # fire when node REACHES inactive state (after configure)
            entities=[ # actions to run on this transition
                EmitEvent( # emit activation event
                    event=ChangeState( # request activate transition
                        lifecycle_node_matcher=matches_action(teleop_node), # target this node
                        transition_id=Transition.TRANSITION_ACTIVATE, # activate: inactive → active
                    )
                ),
            ],
        )
    )

    return LaunchDescription([ # return all actions to the launch system
        teleop_node, # start the node process
        configure_handler, # auto-configure on start
        activate_handler, # auto-activate when inactive
    ])
