from maya import cmds


def get_blendshape_per_cv_values(curve, blendshape):
    attr = blendshape + ".inputTarget[0].inputTargetGroup[0].targetWeights[{}]"
    return [cmds.getAttr(attr.format(i)) for i in range(count_cv(curve))]


def count_cv(curve):
    return cmds.getAttr(curve + '.degree') + cmds.getAttr(curve + '.spans')
