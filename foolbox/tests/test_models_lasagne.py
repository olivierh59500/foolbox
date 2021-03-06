import pytest
import numpy as np
from lasagne.layers import GlobalPoolLayer
from lasagne.layers import InputLayer
import theano.tensor as T

from foolbox.models import LasagneModel


@pytest.mark.parametrize('num_classes', [10, 1000])
def test_lasagne_model(num_classes):
    bounds = (0, 255)
    channels = num_classes

    def mean_brightness_net(images):
        logits = GlobalPoolLayer(images)
        return logits

    images_var = T.tensor4('images', dtype='float32')
    images = InputLayer((None, channels, 5, 5), images_var)
    logits = mean_brightness_net(images)

    model = LasagneModel(
        images,
        logits,
        bounds=bounds)

    test_images = np.random.rand(2, channels, 5, 5).astype(np.float32)
    test_label = 7

    assert model.batch_predictions(test_images).shape \
        == (2, num_classes)

    test_logits = model.predictions(test_images[0])
    assert test_logits.shape == (num_classes,)

    test_gradient = model.gradient(test_images[0], test_label)
    assert test_gradient.shape == test_images[0].shape

    np.testing.assert_almost_equal(
        model.predictions_and_gradient(test_images[0], test_label)[0],
        test_logits)
    np.testing.assert_almost_equal(
        model.predictions_and_gradient(test_images[0], test_label)[1],
        test_gradient)

    assert model.num_classes() == num_classes


@pytest.mark.parametrize('num_classes', [10, 1000])
def test_lasagne_gradient(num_classes):
    bounds = (0, 255)
    channels = num_classes

    def mean_brightness_net(images):
        logits = GlobalPoolLayer(images)
        return logits

    images_var = T.tensor4('images', dtype='float32')
    images = InputLayer((None, channels, 5, 5), images_var)
    logits = mean_brightness_net(images)

    preprocessing = (np.arange(num_classes)[None, None],
                     np.random.uniform(size=(5, 5, channels)) + 1)

    model = LasagneModel(
        images,
        logits,
        preprocessing=preprocessing,
        bounds=bounds)

    epsilon = 1e-2

    np.random.seed(23)
    test_image = np.random.rand(channels, 5, 5).astype(np.float32)
    test_label = 7

    _, g1 = model.predictions_and_gradient(test_image, test_label)

    l1 = model._loss_fn(test_image[None] - epsilon / 2 * g1, [test_label])[0]
    l2 = model._loss_fn(test_image[None] + epsilon / 2 * g1, [test_label])[0]

    # make sure that gradient is numerically correct
    np.testing.assert_array_almost_equal(
        1e4 * (l2 - l1),
        1e4 * epsilon * np.linalg.norm(g1)**2,
        decimal=1)
