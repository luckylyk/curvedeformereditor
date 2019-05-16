import re
from maya import cmds


TARGETWEIGHT_ATTR = {
    "blendShape": "inputTarget[{0}].inputTargetGroup[{0}].targetWeights[{1}]",
    "cluster": "weightList[{0}].weights[{1}]"
}


def find_curve_input_target_index(curve, deformer):
    """
    this function return the input target index of a curve into a deformer.
    To find this index, the function parse the curves connected to the
    deformer attribute: outputGeometry. It find the attribute index where is
    connected the curve. The outputGeometry[index] should match with the
    inputTarget[index]. I guess in some special cases, where an intermediate
    node is plugged between the deformer and the output curve will fail
    the process.
    """
    curveshapes = cmds.listRelatives(
        curve, type='nurbsCurve', noIntermediate=True)
    if curveshapes is None:
        raise ValueError(
            "{} doesn't contains nurbsCurve not intermediate."
            "Impossible to find the input index".format(curve))

    connections = cmds.listConnections(
        deformer + '.outputGeometry', plugs=True, connections=True)
    outputs = [output for i, output in enumerate(connections) if i % 2 == 0]
    inputs = [input_ for i, input_ in enumerate(connections) if i % 2 != 0]
    for input_, output, in zip(inputs, outputs):
        if curveshapes[0] not in input_:
            continue
        target = re.findall(r"outputGeometry\[\d*\]", output)[0]
        index = int([elt for elt in re.findall(r"\d*", target) if elt][0])
        return index


def get_deformer_weights_per_cv(curve, deformer):
    attributename = TARGETWEIGHT_ATTR.get(cmds.nodeType(deformer))
    if attributename is None:
        raise ValueError("deformer is not supported: {}".format(deformer))
    index = find_curve_input_target_index(curve, deformer)
    attr = deformer + "." + attributename
    return [
        cmds.getAttr(attr.format(index, i))
        for i in range(count_cv(curve))]


def set_deformer_weights_per_cv(curve, deformer, values):
    attributename = TARGETWEIGHT_ATTR.get(cmds.nodeType(deformer))
    if attributename is None:
        raise ValueError("deformer is not supported: {}".format(deformer))
    index = find_curve_input_target_index(curve, deformer)
    attr = deformer + "." + attributename
    for i, v in enumerate(values):
        cmds.setAttr(attr.format(index, i), v)


def count_cv(curve):
    return cmds.getAttr(curve + '.degree') + cmds.getAttr(curve + '.spans')
