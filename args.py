import torch
import albumentations as tfms

class Args:

	##############################
	###### Hyperparameters #######
	##############################

	epochs = 30                     # DEFAULT 30 (int 1-99)
	initial_lr = 1e-5               # DEFAULT 1e-5 (float)
	batch_size = 16                 # DEFAULT 16 (int)
	
	arch = "inceptionv4"            # DEFAULT resnet152 (resnet50 | resnet152 | senet154 | inceptionv4)

	img_size = None                 # DEFAULT None (None | int 224-1024)
	full_size = False               # DEFAULT False (bool)
	use_external = False            # DEFAULT False (bool)
	img_channels = "rgby"           # DEFAULT g (str {r, g, b, y})

	loss = "softmargin"             # DEFAULT softmargin (softmargin | focal | fbeta)
	focal_gamma = 2                 # DEFAULT 2 (float)
	fbeta = 1                       # DEFAULT 1 (float)

	weight_mode = "inverse"         # DEFAULT inverse ({inverse, sqrt} | None)
	weight_method = "loss"          # DEFAULT loss (loss | sampling | None)

	device_ids = [0,1]              # DEFAULT [0,] (list int 0-8)
	workers = 8                     # DEFAULT 8 (int 0-16)

	log_freq = 5                    # DEFAULT 10 (int)
	trainval_ratio = 0.90           # DEFAULT 0.9
	n_val_samples = None            # DEFAULT None (int | None)

	train_augmentation = tfms.Compose([
		tfms.HorizontalFlip(p=0.5),
		tfms.VerticalFlip(p=0.5),
		tfms.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.2, rotate_limit=20),
		tfms.RandomBrightnessContrast(),
		tfms.GaussNoise(var_limit=(2, 8))
	])

	##############################
	########### Test #############
	##############################

	test_augmentation = []        # DEFAULT [] (list)
	test_postprocessing = False   # DEFAULT False (bool)

	##############################
	########## Paths #############
	##############################

	primary_datapath  = ""
	fullsize_datapath = ""
	external_datapath = ""
