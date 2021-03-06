import pyopencl as cl
import numpy as np
from math import *
from __common__ import *
import momo
from momo.features import *

class compute_features( momo.opencl.Program ):
  def __init__( self, convert ):
    momo.opencl.Program.__init__( self )
    self.kernel = self.loadProgram( momo.BASE_DIR + "/opencl/smoke0.cl" )

    self.convert = convert

    mf = cl.mem_flags
    self.direction_buffer = cl.Buffer( self.context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = DIRECTIONS )

  def __call__( self, speed, frame ):
    mf = cl.mem_flags
    features = np.zeros( (8, self.convert.grid_height, self.convert.grid_width, FEATURE_LENGTH ), dtype=np.float32 )

    frame_buffer = cl.Buffer( self.context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf = self.convert.rebase_frame( frame ).astype( np.float32 ) )
    feature_buffer = cl.Buffer( self.context, mf.WRITE_ONLY, features.nbytes )

    self.kernel.computeFeatures( 
      self.queue, features.shape[:-1], None, 
      np.float32( speed ), np.float32( self.convert.delta ),
      self.direction_buffer,
      np.int32( self.convert.grid_width ), np.int32( self.convert.grid_height ), np.int32( FEATURE_LENGTH ),
      np.int32( frame.shape[0] ), frame_buffer, 
      feature_buffer 
    )

    cl.enqueue_copy( self.queue, features, feature_buffer )
    return features

