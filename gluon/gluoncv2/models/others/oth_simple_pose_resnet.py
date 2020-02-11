from __future__ import division

__all__ = ['oth_simple_pose_resnet18_v1b', 'oth_simple_pose_resnet50_v1b', 'oth_simple_pose_resnet101_v1b',
           'oth_simple_pose_resnet152_v1b', 'oth_simple_pose_resnet50_v1d', 'oth_simple_pose_resnet101_v1d',
           'oth_simple_pose_resnet152_v1d', 'oth_resnet50_v1d', 'oth_resnet101_v1d',
           'oth_resnet152_v1d']

import mxnet as mx
from mxnet.context import cpu
from mxnet.gluon.block import HybridBlock
from mxnet.gluon import nn
from mxnet import initializer
import gluoncv as gcv
from gluoncv.data.transforms.pose import get_final_preds


class SimplePoseResNet(HybridBlock):

    def __init__(self,
                 base_name='resnet50_v1b',
                 pretrained_base=False,
                 pretrained_ctx=cpu(),
                 num_joints=17,
                 num_deconv_layers=3,
                 num_deconv_filters=(256, 256, 256),
                 num_deconv_kernels=(4, 4, 4),
                 final_conv_kernel=1,
                 deconv_with_bias=False,
                 in_channels=3,
                 in_size=(256, 192),
                 **kwargs):
        super(SimplePoseResNet, self).__init__(**kwargs)
        assert (in_channels == 3)
        self.in_size = in_size

        from gluoncv.model_zoo import get_model
        base_network = get_model(
            base_name,
            pretrained=pretrained_base,
            ctx=pretrained_ctx,
            norm_layer=gcv.nn.BatchNormCudnnOff)

        self.resnet = nn.HybridSequential()
        if base_name.endswith('v1'):
            for layer in ['features']:
                self.resnet.add(getattr(base_network, layer))
        else:
            for layer in ['conv1', 'bn1', 'relu', 'maxpool', 'layer1', 'layer2', 'layer3', 'layer4']:
                self.resnet.add(getattr(base_network, layer))

        self.deconv_with_bias = deconv_with_bias

        # used for deconv layers
        self.deconv_layers = self._make_deconv_layer(
            num_deconv_layers,
            num_deconv_filters,
            num_deconv_kernels,
        )

        self.final_layer = nn.Conv2D(
            channels=num_joints,
            kernel_size=final_conv_kernel,
            strides=1,
            padding=1 if final_conv_kernel == 3 else 0,
            weight_initializer=initializer.Normal(0.001),
            bias_initializer=initializer.Zero()
        )

    def _get_deconv_cfg(self, deconv_kernel):
        if deconv_kernel == 4:
            padding = 1
            output_padding = 0
        elif deconv_kernel == 3:
            padding = 1
            output_padding = 1
        elif deconv_kernel == 2:
            padding = 0
            output_padding = 0

        return deconv_kernel, padding, output_padding

    def _make_deconv_layer(self,
                           num_layers,
                           num_filters,
                           num_kernels):
        assert num_layers == len(num_filters), \
            'ERROR: num_deconv_layers is different from len(num_deconv_filters)'
        assert num_layers == len(num_kernels), \
            'ERROR: num_deconv_layers is different from len(num_deconv_filters)'

        layer = nn.HybridSequential(prefix='')
        with layer.name_scope():
            for i in range(num_layers):
                kernel, padding, output_padding = \
                    self._get_deconv_cfg(num_kernels[i])

                planes = num_filters[i]
                layer.add(
                    nn.Conv2DTranspose(
                        channels=planes,
                        kernel_size=kernel,
                        strides=2,
                        padding=padding,
                        output_padding=output_padding,
                        use_bias=self.deconv_with_bias,
                        weight_initializer=initializer.Normal(0.001),
                        bias_initializer=initializer.Zero()))
                layer.add(gcv.nn.BatchNormCudnnOff(gamma_initializer=initializer.One(),
                                                   beta_initializer=initializer.Zero()))
                layer.add(nn.Activation('relu'))
                self.inplanes = planes

        return layer

    def hybrid_forward(self, F, x, center=None, scale=None):
        x = self.resnet(x)

        x = self.deconv_layers(x)
        x = self.final_layer(x)

        if center is not None:
            y, maxvals = get_final_preds(x.as_in_context(mx.cpu()), center.asnumpy(), scale.asnumpy())
            return y, maxvals
        else:
            return x


def get_simple_pose_resnet(base_name,
                           pretrained=False,
                           ctx=cpu(),
                           root='~/.mxnet/models',
                           **kwargs):

    net = SimplePoseResNet(base_name, **kwargs)

    if pretrained:
        from gluoncv.model_zoo.model_store import get_model_file
        net.load_parameters(
            get_model_file(
                'simple_pose_%s'%(base_name),
                tag=pretrained,
                root=root),
            ctx=ctx)

    return net


def oth_simple_pose_resnet18_v1b(**kwargs):
    r"""ResNet-18 backbone model from `"Simple Baselines for Human Pose Estimation and Tracking"
    <https://arxiv.org/abs/1804.06208>`_ paper.
    Parameters
    ----------
    pretrained : bool or str
        Boolean value controls whether to load the default pretrained weights for model.
        String value represents the hashtag for a certain version of pretrained weights.
    ctx : Context, default CPU
        The context in which to load the pretrained weights.
    root : str, default '$MXNET_HOME/models'
        Location for keeping the model parameters.
    """
    return get_simple_pose_resnet('resnet18_v1b', **kwargs)

def oth_simple_pose_resnet50_v1b(**kwargs):
    r"""ResNet-50 backbone model from `"Simple Baselines for Human Pose Estimation and Tracking"
    <https://arxiv.org/abs/1804.06208>`_ paper.
    Parameters
    ----------
    pretrained : bool or str
        Boolean value controls whether to load the default pretrained weights for model.
        String value represents the hashtag for a certain version of pretrained weights.
    ctx : Context, default CPU
        The context in which to load the pretrained weights.
    root : str, default '$MXNET_HOME/models'
        Location for keeping the model parameters.
    """
    return get_simple_pose_resnet('resnet50_v1b', **kwargs)

def oth_simple_pose_resnet101_v1b(**kwargs):
    r"""ResNet-101 backbone model from `"Simple Baselines for Human Pose Estimation and Tracking"
    <https://arxiv.org/abs/1804.06208>`_ paper.
    Parameters
    ----------
    pretrained : bool or str
        Boolean value controls whether to load the default pretrained weights for model.
        String value represents the hashtag for a certain version of pretrained weights.
    ctx : Context, default CPU
        The context in which to load the pretrained weights.
    root : str, default '$MXNET_HOME/models'
        Location for keeping the model parameters.
    """
    return get_simple_pose_resnet('resnet101_v1b', **kwargs)

def oth_simple_pose_resnet152_v1b(**kwargs):
    r"""ResNet-152 backbone model from `"Simple Baselines for Human Pose Estimation and Tracking"
    <https://arxiv.org/abs/1804.06208>`_ paper.
    Parameters
    ----------
    pretrained : bool or str
        Boolean value controls whether to load the default pretrained weights for model.
        String value represents the hashtag for a certain version of pretrained weights.
    ctx : Context, default CPU
        The context in which to load the pretrained weights.
    root : str, default '$MXNET_HOME/models'
        Location for keeping the model parameters.
    """
    return get_simple_pose_resnet('resnet152_v1b', **kwargs)

def oth_simple_pose_resnet50_v1d(**kwargs):
    r"""ResNet-50-d backbone model from `"Simple Baselines for Human Pose Estimation and Tracking"
    <https://arxiv.org/abs/1804.06208>`_ paper.
    Parameters
    ----------
    pretrained : bool or str
        Boolean value controls whether to load the default pretrained weights for model.
        String value represents the hashtag for a certain version of pretrained weights.
    ctx : Context, default CPU
        The context in which to load the pretrained weights.
    root : str, default '$MXNET_HOME/models'
        Location for keeping the model parameters.
    """
    return get_simple_pose_resnet('resnet50_v1d', **kwargs)

def oth_simple_pose_resnet101_v1d(**kwargs):
    r"""ResNet-101-d backbone model from `"Simple Baselines for Human Pose Estimation and Tracking"
    <https://arxiv.org/abs/1804.06208>`_ paper.
    Parameters
    ----------
    pretrained : bool or str
        Boolean value controls whether to load the default pretrained weights for model.
        String value represents the hashtag for a certain version of pretrained weights.
    ctx : Context, default CPU
        The context in which to load the pretrained weights.
    root : str, default '$MXNET_HOME/models'
        Location for keeping the model parameters.
    """
    return get_simple_pose_resnet('resnet101_v1d', **kwargs)

def oth_simple_pose_resnet152_v1d(**kwargs):
    r"""ResNet-152-d backbone model from `"Simple Baselines for Human Pose Estimation and Tracking"
    <https://arxiv.org/abs/1804.06208>`_ paper.
    Parameters
    ----------
    pretrained : bool or str
        Boolean value controls whether to load the default pretrained weights for model.
        String value represents the hashtag for a certain version of pretrained weights.
    ctx : Context, default CPU
        The context in which to load the pretrained weights.
    root : str, default '$MXNET_HOME/models'
        Location for keeping the model parameters.
    """
    return get_simple_pose_resnet('resnet152_v1d', **kwargs)


def oth_resnet50_v1d(pretrained=False, **kwargs):
    from gluoncv.model_zoo import get_model
    net = get_model(
        'resnet50_v1d',
        pretrained=pretrained,
        **kwargs)
    net.in_size = (224, 224)
    return net


def oth_resnet101_v1d(pretrained=False, **kwargs):
    from gluoncv.model_zoo import get_model
    net = get_model(
        'resnet101_v1d',
        pretrained=pretrained,
        **kwargs)
    net.in_size = (224, 224)
    return net


def oth_resnet152_v1d(pretrained=False, **kwargs):
    from gluoncv.model_zoo import get_model
    net = get_model(
        'resnet152_v1d',
        pretrained=pretrained,
        **kwargs)
    net.in_size = (224, 224)
    return net


def _test():
    import numpy as np
    import mxnet as mx

    pretrained = False

    models = [
        oth_simple_pose_resnet18_v1b,
        oth_simple_pose_resnet50_v1b,
        oth_simple_pose_resnet101_v1b,
        oth_simple_pose_resnet152_v1b,
        oth_simple_pose_resnet50_v1d,
        oth_simple_pose_resnet101_v1d,
        oth_simple_pose_resnet152_v1d,
        oth_resnet50_v1d,
        oth_resnet101_v1d,
        oth_resnet152_v1d,
    ]

    for model in models:

        net = model(pretrained=pretrained)

        ctx = mx.cpu()
        if not pretrained:
            net.initialize(ctx=ctx)

        x = mx.nd.zeros((1, 3, 256, 192), ctx=ctx)
        y = net(x)
        # assert (y.shape == (1, 17, 64, 48))

        # net.hybridize()
        net_params = net.collect_params()
        weight_count = 0
        for param in net_params.values():
            if (param.shape is None) or (not param._differentiable):
                continue
            weight_count += np.prod(param.shape)
        print("m={}, {}".format(model.__name__, weight_count))
        assert (model != oth_simple_pose_resnet18_v1b or weight_count == 15376721)
        assert (model != oth_simple_pose_resnet50_v1b or weight_count == 33999697)
        assert (model != oth_simple_pose_resnet101_v1b or weight_count == 52991825)
        assert (model != oth_simple_pose_resnet152_v1b or weight_count == 68635473)
        assert (model != oth_simple_pose_resnet50_v1d or weight_count == 34018929)
        assert (model != oth_simple_pose_resnet101_v1d or weight_count == 53011057)
        assert (model != oth_simple_pose_resnet152_v1d or weight_count == 68654705)


if __name__ == "__main__":
    _test()