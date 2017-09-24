import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# Invert binary navigable terrain into obstacles binary image
def to_obstacle(img):
    # Create an array of zeros with the same size as the image
    obstacle = np.zeros_like(img)

    # Create a boolean array with value of "True" when pixel is not navigable
    is_obstacle = img == 0

    # Index the array of zero with the boolean array and set to 1
    obstacle[is_obstacle] = 1
    # Return the single-channel binary image
    return obstacle

# Identify pixel of sample rock
# Threshold of (100,100,0) <= RGB <= (255,255,80) does a good identifying the rocks
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

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the
    # center bottom of the image.
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle)
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))

    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale):
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image

    return warped


# Apply the above functions in succession and update the Rover state accordingly
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