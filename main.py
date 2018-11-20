import os
import glob
import csv
import datetime
import tqdm

import torch
from torch import nn
import torch.nn.functional as F

import torchvision
from torchvision import transforms as tfms

import numpy as np
from PIL import Image
import cv2

import sklearn
from sklearn import metrics

import matplotlib
import matplotlib.pyplot as plt

from loaders.loader import ProteinImageDataset
from models.resnet import PretrainedResNet
from utils.logger import Logger

INITIAL_LR = 0.00002
BATCH_SIZE = 16
EPOCHS     = 30

def main():

	# transforms
	train_transforms = tfms.Compose([
		tfms.RandomHorizontalFlip(),
		tfms.RandomVerticalFlip(),
		tfms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0),
		tfms.ToTensor(),
		tfms.Normalize(mean=[0.054, 0.054, 0.054], std=[0.089, 0.089, 0.089])
	])
	test_transforms = tfms.Compose([
		tfms.ToTensor(),
		tfms.Normalize(mean=[0.054, 0.054, 0.054], std=[0.089, 0.089, 0.089])
	])

	# datasets
	train_dataset = ProteinImageDataset(split="train", transforms=train_transforms, channels="g", debug=False)
	val_dataset   = ProteinImageDataset(split="val",   transforms=test_transforms,  channels="g", debug=False)
	test_dataset  = ProteinImageDataset(split="test",  transforms=test_transforms,  channels="g", debug=False)

	# dataloaders
	train_loader = torch.utils.data.DataLoader(train_dataset, shuffle=True,  batch_size=BATCH_SIZE, num_workers=12, pin_memory=True)
	val_loader   = torch.utils.data.DataLoader(val_dataset,   shuffle=False, batch_size=1,          num_workers=12, pin_memory=True)
	test_loader  = torch.utils.data.DataLoader(test_dataset,  shuffle=False, batch_size=1,          num_workers=12, pin_memory=True)

	model = PretrainedResNet().cuda()
	model = nn.DataParallel(model, device_ids=[0,1])

	loss_func = nn.MultiLabelSoftMarginLoss(weight=train_dataset.class_weights).cuda()
	optimizer = torch.optim.Adam(model.parameters(), lr=INITIAL_LR)

	logger = Logger()
	max_score = 0

	for epoch in range(EPOCHS):
		print("Epoch {}".format(epoch + 1))
		train(model, train_loader, loss_func, optimizer)
		score = evaluate(model, val_loader, loss_func)
		if score > max_score:
			logger.save_model(model, epoch)
			max_score = score

	test_results = test(model, test_loader)
	logger.write_test_results(test_results, test_dataset.test_ids)


def train(model, train_loader, loss_func, optimizer):
	model.train()

	losses = []
	for i, (images, labels) in tqdm.tqdm(enumerate(train_loader), total=len(train_loader)):

		images = images.to(dtype=torch.float32).cuda(non_blocking=True)
		labels = labels.to(dtype=torch.float32).cuda(non_blocking=True)

		outputs = model(images)

		loss = loss_func(outputs, labels)

		optimizer.zero_grad()
		loss.backward()
		optimizer.step()

		losses.append(loss.item())
		if i % (len(train_loader)//5) == 0:
			tqdm.tqdm.write("Train loss: {}".format(np.mean(losses[-10:])))

def evaluate(model, val_loader, loss_func):
	model.eval()

	losses = []
	preds = []
	targets = []

	with torch.no_grad():
		for i, (images, labels) in tqdm.tqdm(enumerate(val_loader), total=len(val_loader)):

			images = images.to(dtype=torch.float32).cuda(non_blocking=True)
			labels = labels.to(dtype=torch.float32).cuda(non_blocking=True)

			outputs = model(images)
			loss = loss_func(outputs, labels).item()

			pred = torch.sigmoid(outputs)
			pred = pred.cpu().numpy()
			pred = (pred > 0.5).astype(np.int)

			if not np.any(pred):
				top = np.argmax(pred, axis=1)
				pred = np.zeros(pred.shape)
				pred[:, top] = 1

			labels = labels.cpu().numpy().astype(np.int)

			losses.append(loss)
			preds.append(pred)
			targets.append(labels)

	targets = np.array(targets).squeeze()
	preds = np.array(preds).squeeze()

	acc = metrics.accuracy_score(targets, preds)
	f1 = metrics.f1_score(targets, preds, average="macro")
	f1_perclass = metrics.f1_score(targets, preds, average=None)
	loss = np.mean(losses)

	print()
	print("Eval")
	print("Evaluation loss:", loss)
	print("Evaluation accuracy:", acc)
	print("Evaluation score:", f1)
	print("Per-Class F1:", f1_perclass)
	print()

	return f1

def test(model, test_loader):
	model.eval()

	preds = []
	with torch.no_grad():
		for i, (image, frame_id) in tqdm.tqdm(enumerate(test_loader), total=len(test_loader)):

			image = image.to(dtype=torch.float32).cuda(non_blocking=True)
			output = model(image)
			output = torch.sigmoid(output)
			output = output.cpu().numpy()

			pred = (output > 0.5).astype(np.int)
			if not np.any(pred):
				top = np.argmax(pred, axis=1)
				pred = np.zeros(pred.shape)
				pred[:, top] = 1
			pred = test_loader.dataset.from_onehot(pred)

			frame_id = frame_id[0]
			preds.append((frame_id, pred))

	return preds

if __name__ == "__main__":
	main()

