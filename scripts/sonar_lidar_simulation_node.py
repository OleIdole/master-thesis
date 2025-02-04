#!/usr/bin/env python
# lidar_restrictions.py

import rospy
import math
from sensor_msgs.msg import LaserScan, Range
from math import *
import numpy as np
import copy
from master_thesis.msg import LaserScanFiltered
from std_msgs.msg import Header
from sensor_msgs.msg import PointCloud2 as pc2
from laser_geometry import LaserProjection
from std_srvs.srv import SetBool, SetBoolResponse

class sonar_lidar_scan_node:
    def __init__(self):

        # Variables
        self.laserProj = LaserProjection()
        self.isWater = False

        # Publishers
        self.pub = rospy.Publisher("/sonar_lidar_state", LaserScanFiltered, queue_size=10)
        self.pcWaterPub = rospy.Publisher("/water_pc", pc2, queue_size=1)

        # Subscribers
        rospy.Subscriber("/scan", LaserScan, self.callback_get_lidar_scan)
        rospy.Subscriber("/sonar", Range, self.callback_get_sonar_scan)

        # Services
        self.service_set_isWater = rospy.Service('is_water', SetBool , self.callback_isWater) # Toggle for isWater when water is classified


        # Defining variables:
        self.scanFiltered = LaserScanFiltered()
        self.scanFiltered.laser_range = 0.0
        self.scanFiltered.laser_intensity = 0.0
        self.scanFiltered.sonar_range = 0.0
        self.sensor_offset = 13.5
        
        rospy.spin()

    def callback_get_lidar_scan(self, data):
        # Convert data to lists
        ranges_filter = list(data.ranges)
        intensities_filter = list(data.intensities)

        # Extract front center scan data
        self.scanFiltered.laser_range = ranges_filter[0] * 100
        self.scanFiltered.laser_intensity = intensities_filter[0]

        # Calculate sensor deviation and publish filtered scan
        self.scanFiltered.deviation = self.scanFiltered.laser_range - self.scanFiltered.sonar_range - self.sensor_offset
        self.pub.publish(self.scanFiltered)

    # Certain things will be different when porting to real environment:
    # Might need to use offset, right now we just use different frame and tf, but this might work
    # in real environment too.
    # Scan values seem correct without multiplying by 100 now, but need to verify this when porting
    # to real environment as well.
    def callback_get_sonar_scan(self, data):
        #self.scanFiltered.sonar_range = data.range * 100
        if(self.isWater == True):
            # Construct LaserScan message
            sonarScanMsg = LaserScan()
            sonarScanMsg.header = data.header
            sonarScanMsg.angle_min = -0.1
            sonarScanMsg.angle_max = 0.1
            sonarScanMsg.angle_increment = 0.1
            sonarScanMsg.range_min = data.min_range
            sonarScanMsg.range_max = data.max_range
            sonarScanMsg.ranges = [data.range, data.range, data.range] # Easy fix because not able to make pointcloud with 1 point.

            # Convert to PointCloud2
            cloud_out = self.laserProj.projectLaser(sonarScanMsg)

            # Publish PointCloud2
            self.pcWaterPub.publish(cloud_out)

    def callback_isWater(self, is_water):
        if is_water.data==True:
            self.isWater = True
            return SetBoolResponse(True, 'Mapping water')
        elif is_water.data==False:
            self.isWater = False
            return SetBoolResponse(True, 'No longer mapping water')

    def handle_offset(self):
        if self.scanFiltered.sonar_range < 6.0:
            self.sensor_offset = 12
        elif self.scanFiltered.sonar_range < 20.0:
            self.sensor_offset = 14.0
        elif self.scanFiltered.sonar_range < 40.0:
            self.sensor_offset = 16.0
        else:
            self.sensor_offset = 20.0


if __name__ == '__main__':
	try:
		rospy.init_node('sonar_lidar_scan')
		sn = sonar_lidar_scan_node()
	except rospy.ROSInterruptException:
		pass