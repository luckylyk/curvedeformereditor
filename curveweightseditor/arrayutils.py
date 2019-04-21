

def set_value(value, index, array, break_point_indices=None, interpolate=True):
    """
    This function set a value in an array. If the interpolate args is False,
    this function do litterally this: array[index] = value
    """
    array = array[:]
    array[index] = value
    if len(array) < 3 or interpolate is False:
        return array
    break_point_indices = break_point_indices or [0, len(array) - 1]
    previous_index, next_index = find_previous_and_next_indices(
        index, break_point_indices)
    array = set_linear_interpolations(array, previous_index, index)
    array = set_linear_interpolations(array, index, next_index)
    return array


def set_linear_interpolations(array, start_index=None, end_index=None):
    """
    This function create an linear interpolation between to indexes in an array
    If no indexes are specified, the start and out point are the first and the
    last array index.
    """
    start_index = start_index or 0
    end_index = end_index or len(array) - 1
    array = array[:]
    start_value = array[start_index]
    end_value = array[end_index]
    difference = abs(start_value - end_value)
    divisor = end_index - start_index
    increment = difference / divisor
    if end_value < start_value:
        increment = -increment
    interpolation = start_value
    for i in range(start_index + 1, end_index):
        interpolation += increment
        array[i] = interpolation
    return array


def find_previous_and_next_indices(index, indices):
    """
    TO TEST AND DOCUMENTATE
    """
    if index == 0:
        return indices[0], indices[1]
    if index == indices[-1]:
        return indices[index - 2], indices[-1]
    if index in indices:
        index = indices.index(index)
        return indices[index - 1], indices[index + 1]
    previous = indices[0]
    for i in indices:
        if i > index:
            return previous, i
        previous = i


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
        if abs(value - boundarie_average) > 1e-3:
            break_indexes.append(i)
        previous_value = value
    return break_indexes


def split_value(value, sample):
    samples = [0]
    sample -= 1
    inc = value / sample
    value = inc
    for _ in range(sample):
        samples.append(value)
        value += inc
    return samples


if __name__ == '__main__':
    def test_get_break_indices():
        values = [1, 2, 3, 4, 5, 7, 9, 11]
        indices = get_break_indices(values)
        assert indices == [0, 4, 7]
        values = [1, 2, 3, 4, 3, 2, 1, 0, -1, 10, 12, 14]
        indices = get_break_indices(values)
        assert indices == [0, 3, 8, 9, 11]
        values = [1, 50]
        indices = get_break_indices(values)
        assert indices == [0, 1]

    def test_set_linear_interpolation_in_values():
        values = [1, 1, 1, 1, 1, 1, 1, 1]
        values_2 = set_linear_interpolations(values, 0, 7)
        assert values_2 == values
        values = [1, 1, 1, 1, 1, 1, 1, 8]
        values_2 = set_linear_interpolations(values, 0, 7)
        assert values_2 == [1, 2, 3, 4, 5, 6, 7, 8]
        values = [8, 1, 1, 1, 1, 1, 1, 1]
        values_2 = set_linear_interpolations(values, 0, 7)
        assert values_2 == [8, 7, 6, 5, 4, 3, 2, 1]
        values = [8, 1, 1, 5, 1, 1, 1, 1]
        values_2 = set_linear_interpolations(values, 3, 7)
        assert values_2 == [8, 1, 1, 5, 4, 3, 2, 1]

    def test_set_value():
        values = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        values_2 = set_value(5, 4, values, break_point_indices=None)
        print(values_2)
        assert values_2 == [1, 2, 3, 4, 5, 4, 3, 2, 1]
        values = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        values_2 = set_value(3, 3, values, break_point_indices=[1, 5])
        print(values_2)
        assert values_2 == [1, 1, 2, 3, 2, 1, 1, 1, 1, 1, 1]

    test_get_break_indices()
    test_set_linear_interpolation_in_values()
    test_set_value()
