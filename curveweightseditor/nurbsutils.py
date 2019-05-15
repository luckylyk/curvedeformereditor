import re
from maya import cmds


TARGETWEIGHT_ATTR = "inputTarget[{0}].inputTargetGroup[{0}].targetWeights[{1}]"


def find_curve_input_target_index(curve, blendshape):
    """
    this function return the input target index of a curve into a blendshape.
    To find this index, the function parse the curves connected to the
    blendshape attribute: outputGeometry. It find the attribute index where is
    connected the curve. The outputGeometry[index] should match with the
    inputTarget[index]. I guess in some special cases, where an intermediate
    node is plugged between the blendshape and the output curve will fail
    the process.
    """
    curveshapes = cmds.listRelatives(
        curve, type='nurbsCurve', noIntermediate=True)
    if curveshapes is None:
        raise ValueError(
            "{} doesn't contains nurbsCurve not intermediate."
            "Impossible to find the input index".format(curve))

    connections = cmds.listConnections(
        blendshape + '.outputGeometry', plugs=True, connections=True)
    outputs = [output for i, output in enumerate(connections) if i % 2 == 0]
    inputs = [input_ for i, input_ in enumerate(connections) if i % 2 != 0]
    for input_, output, in zip(inputs, outputs):
        if curveshapes[0] not in input_:
            continue
        target = re.findall(r"outputGeometry\[\d*\]", output)[0]
        index = int([elt for elt in re.findall(r"\d*", target) if elt][0])
        return index


def get_blendshape_weights_per_cv(curve, blendshape):
    index = find_curve_input_target_index(curve, blendshape)
    attr = blendshape + "." + TARGETWEIGHT_ATTR
    return [
        cmds.getAttr(attr.format(index, i))
        for i in range(count_cv(curve))]


def set_blendshape_weights_per_cv(curve, blendshape, values):
    index = find_curve_input_target_index(curve, blendshape)
    attr = blendshape + "." + TARGETWEIGHT_ATTR
    for i, v in enumerate(values):
        cmds.setAttr(attr.format(index, i), v)


def get_cluster_weights_per_cv(curve, cluster):
    # TODO
    pass


def set_cluster_weights_per_cv(curve, cluster):
    # TODO
    pass


def count_cv(curve):
    return cmds.getAttr(curve + '.degree') + cmds.getAttr(curve + '.spans')
