from __future__ import annotations

import logging

from .. import _expr_graph as unit_graph

_log = logging.getLogger(__name__)


class DecipherDateRef(unit_graph.Visitor):
    """
    Inspect the visited graph to determine if the graph represents a
    date or rather is a simple unit shift.

    Note that there are some interesting cases:

        $ udunits2 -H 'meter days since 2000' -W 'meter days since 2001'
            1 meter days since 2000 = 0 (meter days since 2001)
            x/(meter days since 2001) = (x/(meter days since 2000)) - 1
        $ udunits2 -H 'meter days since 2000-01' -W 'meter days since 2001-01'
            udunits2: Don't recognize "meter days since 2000-01"
        $ udunits2 -H 'days since 2000' -W 'days since 2001'
            1 days since 2000 = -365 (days since 2001)
            x/(days since 2001) = (x/(days since 2000)) - 366
        $ udunits2 -H 'meter (days since 2000)' -W 'meter (days since 2001)'
            1 meter (days since 2000) = 1 (meter (days since 2001))
            x/(meter (days since 2001)) = (x/(meter (days since 2000)))
        $ udunits2 -H 'meter meter-1 days since 2000' -W 'meter meter-1 days since 2001'
            1 meter meter-1 days since 2000 = -365 (meter meter-1 days since 2001)
            x/(meter meter-1 days since 2001) = (x/(meter meter-1 days since 2000)) - 366
        $ udunits2 -H '(weeks since 2001) (days since 2000)' -W '(weeks since 2001) (days since 2001)'
            1 (weeks since 2001) (days since 2000) = 1 ((weeks since 2001) (days since 2001))
            x/((weeks since 2001) (days since 2001)) = 1*(x/((weeks since 2001) (days since 2000)))
        $ udunits2 -H 'kilodays since 2000-01' -W 'days since 2001-01'
            1 kilodays since 2000-01 = 634 (days since 2001-01)
            x/(days since 2001-01) = 1000*(x/(kilodays since 2000-01)) - 366

    This visitor's responsibility is to strip out the date-like unit definitions and replace
    them with references (date, date_1, date_2 etc.).


    IN: "meter days since 2001-01"
    OUT: Invalid date unit exception.

    IN: "meter days since 2001"
    OUT: "meter days since 2001", {}  # Not a date.

    IN: "meter meter-1 days since 2001"
    OUT: "meter meter-1 date", {'date': ('days', '2001')}

    IN: "(weeks since 2001) (days since 2000)"
    OUT: "(date) (date_2)", {'date': ('weeks', '2001'), 'date_2': ('days', '2000')}

    IN: "kilodays since 2001"
    OUT: "date", {'date': ('kilodays', '2001')}

    """
