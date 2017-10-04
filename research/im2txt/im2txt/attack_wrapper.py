# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Model wrapper class for performing attack with a ShowAndTellModel."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import tensorflow as tf
from tensorflow.python.framework import graph_util
import numpy as np
import math


from im2txt import show_and_tell_model
from im2txt.inference_utils import inference_wrapper_base

class AttackWrapper(inference_wrapper_base.InferenceWrapperBase):
  """Model wrapper class for performing attack with a ShowAndTellModel."""

  def __init__(self):
    super(AttackWrapper, self).__init__()

  def build_model(self, model_config):
    model = show_and_tell_model.ShowAndTellModel(model_config, mode="attack")
    model.build()
    self.model = model
    return model

  def feed_image(self, sess, encoded_image):
    initial_state = sess.run(fetches="lstm/initial_state:0",
                             feed_dict={"image_feed:0": encoded_image})
    return initial_state

  # input feed, mask_feed and image_feed are numpy arrays
  # returns a number
  def attack_step(self, sess, input_feed, mask_feed, image_raw_feed):
    grad_op = tf.gradients(self.model.target_cross_entropy_losses, self.model.images)
    grads, target_cross_entropy_losses = sess.run(
        fetches=[grad_op, self.model.target_cross_entropy_losses],
        feed_dict={
            "input_feed:0": input_feed,
            "input_mask:0": mask_feed,
            "image_raw_feed:0": image_raw_feed
        })
    # print(grads)
    print(target_cross_entropy_losses)
    return math.exp(-np.sum(target_cross_entropy_losses))

  # input feed, mask_feed and image_feed are tensors
  # returns a tensor
  def predict(self, sess, input_feed, mask_feed, image_raw_feed):
    # model_graph_def = sess.graph.as_graph_def()
    # model_meta_graph = tf.train.export_meta_graph(clear_extraneous_savers = True)
    model_meta_graph = tf.train.export_meta_graph()
    """
    frozen_model_graph_def = graph_util.convert_variables_to_constants(sess,
            # model_graph_def,
            model_meta_graph.graph_def,
            ["softmax_and_cross_entropy/softmax_and_cross_entropy"])
    sum_log_probs = tf.import_graph_def(
            frozen_model_graph_def,
            input_map={
              "input_feed:0": input_feed,
              "input_mask:0": mask_feed,
              "image_raw_feed:0": image_raw_feed
              },
            return_elements=[self.model.target_cross_entropy_losses.name])
    """
    saver = tf.train.import_meta_graph(
            model_meta_graph,
            import_scope="import",
            input_map={
              "input_feed:0": input_feed,
              "input_mask:0": mask_feed,
              "image_raw_feed:0": image_raw_feed
              })
    sum_log_probs = sess.graph.get_tensor_by_name("import/softmax_and_cross_entropy/softmax_and_cross_entropy:0")
    return sum_log_probs

  '''
  def new_caption_prob(self, sess, cap_sentence, encoded_image):
    logprob=0.0
    state_feed = self.feed_image(sess, encoded_image)
    state_feed = np.array([state_feed[0]])
    for i in range(len(cap_sentence)-1):
      input_feed = np.array([cap_sentence[i]])

      softmax, new_state, metadata = self.attack_step(sess,input_feed,np.ones(np.shape(input_feed)),encoded_image)
      state_feed = new_state
      next_word_probability = softmax[0][cap_sentence[i+1]]
      logprob = logprob + math.log(next_word_probability)
    return math.exp(logprob)
  '''
  

  
    
