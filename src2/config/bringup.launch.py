#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory as get_dir
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument as DeclArg
from launch.substitutions import LaunchConfiguration as LConf
from launch_ros.actions import Node


def generate_launch_description():
    cfg_f = os.path.join(get_dir("atlas_bringup"), "config", "atlas_params.yaml")
    a1, a2, a3 = (
        DeclArg("use_sim_time", default_value="false"),
        DeclArg("mission_profile", default_value="PROFILE_A"),
        DeclArg("params_file", default_value=cfg_f),
    )
    u_sim, m_prof, p_fil = (
        LConf("use_sim_time"),
        LConf("mission_profile"),
        LConf("params_file"),
    )
    n1 = Node(
        package="atlas_autonomy",
        executable="state_machine_node.py",
        name="atlas_state_machine",
        output="screen",
        respawn=True,
        respawn_delay=2.0,
        parameters=[p_fil, {"use_sim_time": u_sim, "mission_profile": m_prof}],
    )
    n2 = Node(
        package="atlas_autonomy",
        executable="path_planner_node.py",
        name="atlas_path_planner",
        output="screen",
        respawn=True,
        respawn_delay=2.0,
        parameters=[p_fil, {"use_sim_time": u_sim}],
    )
    n3 = Node(
        package="atlas_hardware",
        executable="pwm_mixer_node.py",
        name="atlas_pwm_mixer",
        output="screen",
        respawn=True,
        respawn_delay=1.0,
        parameters=[p_fil, {"use_sim_time": u_sim}],
    )
    n4 = Node(
        package="atlas_hardware",
        executable="ds18b20_node.py",
        name="atlas_temp_sensor",
        output="screen",
        respawn=True,
        respawn_delay=5.0,
        parameters=[p_fil, {"use_sim_time": u_sim}],
    )
    return LaunchDescription([a1, a2, a3, n1, n2, n3, n4])
