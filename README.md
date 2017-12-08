# Udacity Robotics Nanodegree - Rover Project
[//]: # (Image References)

[graphic-setting]: ./images/graphic-setting.png
[color-thresholding]: ./images/color-thresholding.png
[perspective-transform-1]: ./images/perspective-transform-1.png
[perspective-transform-2]: ./images/perspective-transform-2.png
[rover-drive]: ./images/rover-drive.png
[perception-video]: ./output/test_mapping.mp4

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.

---
## Quickstart
1. To access the notebook, you need to go inside the `code` directory and run
 the following command in your shell:
 ```shell
 > jupyter notebook rover_project_test_notebook.ipynb
 ```
2. To enable autonomous mode in the simulator, you need to go inside the `code`
 directory and run the following command in your shell:
 ```shell
 > python drive_rover.py
 ```

## Simulator Setting
The graphic setting when image data recorded is portrayed below:
![Graphic Setting Image][graphic-setting]

## Writeup

### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one. You can submit your writeup as markdown or pdf. Here is a template writeup for this project you can use as a guide and a starting point.

You're reading it!

## Notebook Analysis

### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.

The following is the overall result on color thresholding process for which to filter input image to output binary image that contains either navigable terrain, obstacles, or rocks:

![Color Thresholding Image][color-thresholding]

### Obstacle Identification
The function `to_obstacle()` is added in the notebook and it receives binary
image from the output of `navigable_threshold()` functon. Here's the code:

```python
def to_obstacle(img):
    # Create an array of zeros with the same size as the image
    obstacle = np.zeros_like(img)
    
    # Create a boolean array with value of "True" when pixel is not navigable
    is_obstacle = img == 0
            
    # Index the array of zero with the boolean array and set to 1
    obstacle[is_obstacle] = 1
    # Return the single-channel binary image
    return obstacle
```

The way `to_obstacle()` identifies obstacles is by first creating a boolean array to target the negation of navigable terrain from input image. Then a binary image is created and set to have the value of `1` where the boolean array index is `True`. This way, the returned binary image will depict everything else that is not navigable (obstacles).

### Rock Identification
The function `sample_rock_threshold()` is added in the notebook and it receives
an RGB image that would be going through a series of analysis to filter rock
samples and returning a binary image containing rock samples. Here's the code:

```python
def sample_rock_threshold(img, low_thresh=(170, 120, 0), high_thresh=(230, 180, 60)):
    # Create an array of zeros same xy size as img, but single channel
    rock = np.zeros_like(img[:,:,0])
    
    # Create a boolean array with value of "True" when threshold is met
    within_threshold = ((img[:,:,0] >= low_thresh[0]) & (img[:,:,0] <= high_thresh[0] )) \
                    & ((img[:,:,1] >= low_thresh[1]) & (img[:,:,1] <= high_thresh[1] )) \
                    & ((img[:,:,2] >= low_thresh[2]) & (img[:,:,2] <= high_thresh[2] ))
            
    # Index the array of zeros with the boolean array and set to 1
    rock[within_threshold] = 1
    # Return the binary image
    return rock
```

The way `sample_rock_threshold()` identifies rocks is by first creating a boolean array that will evaluate whether the RGB value is within the threshold: (170, 120, 0) <= (R, G, B) <= (230, 100, 60). Then a binary image is created and set to have the value of `1` where the boolean array index is `True`. This method will depict anything in the image that has the color property of the rocks in the simulator.

### 2. Populate the process_image() function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap. Run process_image() on your test data using the moviepy functions provided to create video output of your result.

### `process_image()`
The `process_image()` function is filled with the following steps:
1. Creating a scaffold image/a blank image to be returned as a mosaic image
2. Apply color thresholding to identify navigable terrain/obstacles/rock samples. This is done prior to perspective transform, so that the rover-vision image would have only the obstacles with the color red and not the black pixels from the warped images. Here's the code responsible for it:
  ```python
  # 2) Apply color threshold to identify navigable terrain/obstacles/rock samples
  navigable = navigable_threshold(img)
  obstacle = to_obstacle(navigable)
  rock = sample_rock_threshold(img)
  ```
3. Apply perspective transform. Here's the code:
  ```python
  navigable_warped = perspect_transform(navigable, source, destination)
  obstacle_warped = perspect_transform(obstacle, source, destination)
  rock_warped = perspect_transform(rock, source, destination)
  ```
  Also, here's how the navigable terrain and the rock samples get filtered and being transformed perpectively:
  #### Navigable Terrain
  ![Navigable terrain filter and perspective transformed][perspective-transform-1]

  #### Rock Sample
  ![Rock sample filter and perpective transformed][perspective-transform-2]
4. Create the rover-vision image to be displayed at the top left corner of the mosaic image. Here's the code responsible in doing it:
  ```python
  vision_image = np.zeros((160, 320, 3), dtype=np.float)
  vision_image[:,:,0] = obstacle_warped*255
  vision_image[:,:,1] = rock_warped*255
  vision_image[:,:,2] = navigable_warped*255
  ```
  
5. Obtain world coordinates of the rover-vision by first obtaning the rover-centric coordinates. Here's the code:
  ```python
  # Obtain rover-centric pixel coordinates of navigable terrain/obstacles/rock samples
  navigable_xpix, navigable_ypix = rover_coords(navigable_warped)
  obstacle_xpix, obstacle_ypix = rover_coords(obstacle_warped)
  rock_xpix, rock_ypix = rover_coords(rock_warped)
  
  # Obtain world coordinates of navigable terrain/obstacles/rock samples
  navigable_x_world, navigable_y_world =  pix_to_world(navigable_xpix, navigable_ypix, data.xpos[data.count], data.ypos[data.count], data.yaw[data.count], data.worldmap.shape[0], 10)
  obstacle_x_world, obstacle_y_world =  pix_to_world(obstacle_xpix, obstacle_ypix, data.xpos[data.count], data.ypos[data.count], data.yaw[data.count], data.worldmap.shape[0], 10)
  rock_x_world, rock_y_world =  pix_to_world(rock_xpix, rock_ypix, data.xpos[data.count], data.ypos[data.count], data.yaw[data.count], data.worldmap.shape[0], 10)
  ```

6. Update the worldmap image, overlay it with the groundmap, and display it at
the bottom center of the mosaic image

The following is the resulting video from the `process_image()` function:

![Output video from process_image() function on input images][perception-video]

## Autonomous Navigation and Mapping

### 1. Fill in the perception_step() (at the bottom of the perception.py script) and decision_step() (in decision.py) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

### `perception_step()`
The perception step in `perception.py` differs slightly from the one in the notebook to achieve better fidelity. Here's the overall code:

```python
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO:
    # NOTE: camera image is coming to you in Rover.img
    # 1) Define source and destination points for perspective transform
    source = np.float32([[14, 140],[301, 140],[200, 96],[118, 96]])
        # Destination box size
    dst_size = 5
    bottom_offset = 6
    destination = np.float32([[Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - bottom_offset],
             [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - bottom_offset],
             [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - (dst_size*2) - bottom_offset],
             [Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - (dst_size*2) - bottom_offset]])

    # 2) Apply color threshold to identify navigable terrain/obstacles/rock samples
    navigable = color_thresh(Rover.img)
    obstacle = to_obstacle(navigable)
    rock = sample_rock_threshold(Rover.img)

    # 3) Apply perspective transform
    obstacle_warped = perspect_transform(obstacle, source, destination)
    navigable_warped = perspect_transform(navigable, source, destination)
    rock_warped = perspect_transform(rock, source, destination)

    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        # Render obstacles that are within a rectangular area in front of the rover
    obstacle_warped[:110] = 0
    obstacle_warped[:,:130] = 0
    obstacle_warped[:,190:] = 0
        # Render navigable terrain that are only within 80 meters in front of the rover
    navigable_warped[:80] = 0

    Rover.vision_image[:,:,0] = obstacle_warped*255
    Rover.vision_image[:,:,1] = rock_warped*255
    Rover.vision_image[:,:,2] = navigable_warped*255

    # 5) Convert map image pixel values to rover-centric coords
    navigable_xpix, navigable_ypix = rover_coords(navigable_warped)
    rock_xpix, rock_ypix = rover_coords(rock_warped)
    obstacle_xpix, obstacle_ypix = rover_coords(obstacle_warped)

    # 6) Convert rover-centric pixel values to world coordinates
    navigable_x_world, navigable_y_world = pix_to_world(navigable_xpix, navigable_ypix, \
        Rover.pos[0], Rover.pos[1], Rover.yaw, Rover.worldmap.shape[0], 10)
    rock_x_world, rock_y_world = pix_to_world(rock_xpix, rock_ypix, Rover.pos[0], Rover.pos[1], \
        Rover.yaw, Rover.worldmap.shape[0], 10)
    obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_xpix, obstacle_ypix, Rover.pos[0], \
        Rover.pos[1], Rover.yaw, Rover.worldmap.shape[0], 10)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
        # Setting the rock coordinate to be the one closest to the rover
    if rock_warped.any():
        rock_dist, rock_ang = to_polar_coords(rock_xpix, rock_ypix)
        rock_idx = np.argmin(rock_dist)
        rock_x_closest = rock_x_world[rock_idx]
        rock_y_closest = rock_y_world[rock_idx]
        # Set the worldmap coordinate for rock
        Rover.worldmap[rock_y_closest, rock_x_closest, 1] = 255


    Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
    Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 10

    # 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles
    rover_centric_pixel_distances, rover_centric_angles = to_polar_coords(navigable_xpix, navigable_ypix)
    Rover.nav_dists = rover_centric_pixel_distances
    Rover.nav_angles = rover_centric_angles

    return Rover
```

Here's a step-by-step walkthrough of the code and how it differs from the one in the notebook:
1. Defining source and destination points for perspective transform process
2. Applying color thresholds to obtain navigable terrain, obstacles, and rocks filters.
3. Applying perspective transform to those three filters.
4. Updating Rover.vision_image, but with a modification for the filters:
  - For the obstacle filter, I decided to only to count the 5mx5m rectangular area in front of the rover by the following code:
    ```python
    # Render obstacles that are within a rectangular area in front of the rover
    obstacle_warped[:110] = 0
    obstacle_warped[:,:130] = 0
    obstacle_warped[:,190:] = 0
    ```
    This is done in the hope having a better fidelity of the map.
  - For the navigable terrain filter, I decided to only count the navigable terrain within 8 meters in front of the rover by the following code:
    ```python
    navigable_warped[:80] = 0
    ```
5. Converting filters pixel values to rover-centric coordinates
6. Converting filters' rover-centric coordinates to world coordinates
7. Updating world map with the filters, but only the closest pixel of the rock gets to be in the map for improved accuracy. Here's the code responsible for it:
  ```python
  # Setting the rock coordinate to be the one closest to the rover
  if rock_warped.any():
      rock_dist, rock_ang = to_polar_coords(rock_xpix, rock_ypix)
      rock_idx = np.argmin(rock_dist)
      rock_x_closest = rock_x_world[rock_idx]
      rock_y_closest = rock_y_world[rock_idx]
      # Set the worldmap coordinate for rock
      Rover.worldmap[rock_y_closest, rock_x_closest, 1] = 255
  ```
8. Converting rover-centric pixel positions to polar coordinates for steering.

### `decision_step()`
A slight modification from the default code has been made to make the rover stop when it is near sample. Here's the code:
```python
# Implement conditionals to decide what to do given perception data
# Here you're all set up with some basic functionality but you'll need to
# improve on this decision tree to do a good job of navigating autonomously!

# Example:
if Rover.near_sample:
    Rover.mode = 'stop'

# Check if we have vision data to make decisions with
if Rover.nav_angles is not None:
    # Check for Rover.mode status
    if Rover.mode == 'forward':
        # Stop when rover is near a rock
        if Rover.near_sample:
            Rover.mode = 'stop'
```

### `telemetry()`
Another modification is made for the `telemetry()` function, on which I specified that the perception step would only be executed when Rover's roll & pitch are close to 0. Here's the code responsible for it under `drive_rover.py`:
```python
if np.isfinite(Rover.vel):
    # Execute the perception and decision steps to update the Rover's state
        # Execute perception only when Rover's roll & pitch are close to 0
    if ((Rover.pitch < 1.5) | (Rover.pitch > 358.5)) & \
        ((Rover.roll < 1.5) | (Rover.roll > 358.5)):
        Rover = perception_step(Rover)
    Rover = decision_step(Rover)
```

### 2. Launching in autonomous mode your rover can navigate and map autonomously. Explain your results and how you might improve them in your writeup.

Using the code from `perception.py` and `decision.py`, I have managed to get the >40% world mapped with >60% fidelity and at least 1 rock sample located:

![Rover drive result][rover-drive]