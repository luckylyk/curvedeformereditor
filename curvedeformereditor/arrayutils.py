

def clamp(value, minimum, maximum):
    if value > maximum:
        return maximum
    if value < minimum:
        return minimum
    return value


def get_break_indices(array):
    """
    This function parse a list of numerical values (int, long, float).
    It return the indice in the list where the value is not an linear
    interpolation of the adjacent values. The 0 and the last index are
    everytime returned.
    e.g.
    |                 .     .
    |           .            .
    |      .                  .
    |  .                       .
    ___________________________________
    This will return the indices 0, 3, 4 and 7
    """
    break_indexes = []
    for i, value in enumerate(array):
        if i == 0:
            previous_value = value
            break_indexes.append(i)
            continue
        if i == len(array) - 1:
            break_indexes.append(i)
            break
        next_value = array[i + 1]
        boundarie_average = (next_value + previous_value) / 2.0
        if abs(value - boundarie_average) > 1e-2:
            break_indexes.append(i)
        previous_value = value
    return break_indexes


def split_value(value, sample):
    """
    This array utils split a float in list of sample from 0 to the given value.
    e.g. split_value(100, 10) will return a list of 10 sample from 0 to 100
    with an equal difference :
    [0.0, 11.11, 22.22, 33.33, 44.44, 55.55, 66.66, 77.77, 88.88, 100.0]
    """
    increment = value / (sample - 1)
    return [increment * i for i in range(sample)]
