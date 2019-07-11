import fileinput


class TimeRange(object):
    """Represents a time range (the time between a start time and an end time)

    Example usage:
        >>> time_range = TimeRange('3-5')
        >>> print(time_range.start)
        3.0
        >>> print(time_range.end)
        5.0
        >>> print(time_range.end - time_range.start)
        2.0
    """

    def __init__(self, range_string):
        # for example, convert "3-5" into start=3.0 and end=5.0
        self.start, self.end = [float(time) for time in range_string.split('-')]

def open_hours_ratio(query_time_range, open_hours):
    """
    Inputs:
        A time range to query for (as a TimeRange object)
        A business's open hours (as a list of TimeRanges)

    Output:
        The fraction OF THE QUERY TIME RANGE that the business is open.
        (In other words, the percentage of the query time range in which the business is open.)
        Return this number as a float. This function should NOT do any rounding.

    Examples of time ranges:
        (0, 24)        the whole day
        (9, 17)        9 AM to 5 PM
        (18, 23.75)    6 PM to 11:45 PM

    Examples of open hours:
        []                       closed the entire day
        [(0, 24)]                open the entire day
        [(9.5, 17)]              open from 9:30 AM to 5 PM
        [(11, 14), (18, 22)]     open from 11 AM to 2 PM, and from 6 PM to 10 PM

    Assume that the open hours time ranges are in order and non-overlapping.

    Furthermore, all time ranges (start, end) have the property 0 <= start < end <= 24.

    Examples:
        Query Time Range    Open Hours            Answer
        (4, 10)             [(0, 24)]             1.0
        (7, 11)             [(9, 17)]             0.5
        (0, 24)             [(0, 2), (20, 24)]    0.25
        (5, 22)             []                    0.0
    """
    # TODO: COMPLETE ME
    total_open_hours = 0
    for x in open_hours:
        if x.start >= query_time_range.start:
            a = x.start
        else:
            a = query_time_range.start
        
        if x.end >= query_time_range.end:
            b = query_time_range.end
        else:
            b = x.end
        num = b - a
      #  print(f'num: {num}')
        total_open_hours += num
      #  print(f'total_open_hours: {total_open_hours}')
   # print(f'total_open_hours: {total_open_hours}')

    time_range_hours = query_time_range.end - query_time_range.start
   # print(f'time_range_hours: {time_range_hours}')

    return total_open_hours/time_range_hours

if __name__ == "__main__":
    # input handling
    # lines = list(fileinput.input())
    # input_line_1 = lines[0].strip()
    # input_line_2 = lines[1].strip()
    # query_time_range = TimeRange(input_line_1)
    # if input_line_2:
    #     # for example, convert "1-3, 5-7" into [(1, 3), (5, 7)]
    #     open_hours = [TimeRange(range_string) for range_string in input_line_2.split(', ')]
    # else:
    #     # if the input string is empty, then the business is never open
    #     open_hours = []

    # compute answer and display to 2 decimal places
    #ratio = open_hours_ratio(query_time_range, open_hours)
    input_line_2 = '9-17'
    open_hours = [TimeRange(range_string) for range_string in input_line_2.split(', ')]
    ratio = open_hours_ratio(TimeRange('7-11'), open_hours)
    print('{:.2f}'.format(ratio))