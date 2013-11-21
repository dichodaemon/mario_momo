#!/usr/bin/env python
import rospy
import numpy as np
from pedsim_msgs.msg import AgentState
from pedsim_msgs.msg import AllAgentsState
from pedsim_srvs.srv import SetAgentState
import ast

import sys
import os

BASE_DIR = os.path.abspath( os.path.join( os.path.dirname( __file__ ), ".." ) )
path     = os.path.abspath( os.path.join( BASE_DIR, "python" ) )
sys.path.append( path )

import momo

class Params( object ): pass

def param( name, default = None ):
  if default != None:
    return rospy.get_param( "/" + rospy.get_name() + "/"  + name, default )
  else:
    return rospy.get_param( "/" + rospy.get_name() + "/"  + name )

def get_params():
  result = Params()
  result.target_id = param( "target_id" )
  result.feature_type = param( "feature_type" )
  result.feature_params = ast.literal_eval( param( "feature_params" ) )
  result.weights = np.array( ast.literal_eval( param( "weights" ) ), dtype = np.float64 )
  result.goal = np.array( ast.literal_eval( param( "goal" ) ), dtype = np.float64 )
  result.speed = param( "speed" )
  result.cell_size = param( "cell_size" )
  result.x1   = param( "x1" )
  result.x2   = param( "x2" )
  result.y1   = param( "y1" )
  result.y2   = param( "y2" )
  return result

def plan( feature_type, feature_params, x1, y1, x2, y2, cell_size, robot, other, goal, speed ):
  # Build planning objects
  convert = momo.convert( { "x1": x1, "y1": y1, "x2": x2, "y2": y2 }, cell_size )
  features = momo.features.__dict__[feature_type]
  compute_features = features.compute_features( convert, **feature_params )
  compute_costs = momo.features.compute_costs( convert )
  planner = momo.planning.dijkstra()

  # Compute features and costs
  f = compute_features( speed, other )
  costs = compute_costs( f, parms.weights )

  # Plan

  current = convert.from_world2( robot )
  goal = convert.from_world2( parms.goal )

  cummulated, parents = planner( costs, goal )
  path = planner.get_path( parents, current )

  world_path = []
  for p in path:
    world_path.append( convert.to_world2( p, speed ) )

  interpolated_path = []
  i = 0
  current = robot

  while True:
    current_cell = convert.from_world2( current )
    next_cell = convert_from_world2( world_path[i] )
    if current_cell == next_cell:
      j += 1
    if not j < len( interpolated_path ):
      break
    current[2:] = world_path[i][:2] - current[:2] 
    current[2:] = speed * current[2:] / np.linalg.norm( current[2:] )
    current[:2] += current[2:]
    interpolated_path.append( current * 1.0 )
  return interpolated_path


def set_agent_state( agent_id, x, y, vx, vy ):
    a = AgentState()
    a.id = parms.target_id
    a.position.x = x
    a.position.y = y
    a.velocity.x = vx
    a.velocity.y = vy

    rospy.loginfo( "Waiting to send command: %f, %f, %f, %f" % ( x, y, vx, vy ) )
    rospy.wait_for_service( "SetAgentState" )
    try:
      set_agent_status = rospy.ServiceProxy( "SetAgentState", SetAgentState )
      result = set_agent_status( a )
    except rospy.ServiceException, e:
      rospy.logerr( "Service call failed: %s" % e )
    rospy.loginfo( "Command sent" )

def callback( data ):
  if rospy.get_rostime().to_sec() - data.header.stamp.to_sec() > 0.05: 
    return
  parms = get_params()

  other = []
  robot  = None

  for a in data.agent_states:
    v = np.array( [a.position.x, a.position.y, a.velocity.x, a.velocity.y], dtype = np.float64 )
    if a.id == parms.target_id:
      robot = v
    else:
      other.append( v )
  other = np.array( other )

  path = plan( 
    parms.feature_type, parms.feature_params, 
    parms.x1, parms.y1, parms.x2, parms.y2, parms.cell_size, 
    robot, other, goal, parms.speed 
  )


  if len( path ) > 1:
    set_agent_state( parms.target_id, robot[0], robot[1], result[1][0] - robot[0], result[1][1] - robot[1] )



def listener():
  rospy.init_node( 'irl_features' )
  p = get_params()
  rospy.Subscriber( "AllAgentsStatus", AllAgentsState, callback )
  rospy.spin()


if __name__ == '__main__':
  listener()
