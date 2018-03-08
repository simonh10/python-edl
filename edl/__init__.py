#-*- coding: utf-8 -*-
"""
Python EDL parsing library
"""
import sys
import collections
import re
import pprint
import timecode

from .version import __version__


class List(object):
    """The EDL it self.

    Holds :class:`.Event` instances. It can be indexed to reach each of the
    :class:`.Event`\ s like::

      >>> l = List('25')
      >>> l.append(Event())
      >>> l[0]
      <edl.edl.Event object at 0x7fb630564490>

    :param str fps: The frame per second setting for for this EDL. Should be a
      string one of ['23.98', '24', '25', '29.97', '30', '50', '59.94', '60'].
      `fps` can not be skipped.
    """

    def __init__(self, fps):
        self.events = []
        self.fps = fps
        self.title = ''
        self.fcm = None

    def __getitem__(self, i):
        """Returns each of the Events that this List holds.
        """
        return self.events[i]

    # def __repr__(self):
    #     rep = ["event(\n"]
    #     for e in self.events:
    #         rep.append(e.__repr__())
    #     rep.append(')')
    #     return ''.join(rep)

    def __len__(self):
        return len(self.events)

    def get_start(self):
        start_tc = None
        for e in self.events:
            if start_tc is None:
                start_tc = e.rec_start_tc
            else:
                if e.rec_start_tc.frames < start_tc.frames:
                    start_tc = e.rec_start_tc
        return start_tc

    def get_end(self):
        end_tc = None
        for e in self.events:
            if end_tc is None:
                end_tc = e.rec_end_tc
            else:
                if e.rec_end_tc.frames > end_tc.frames:
                    end_tc = e.rec_end_tc
        return end_tc

    def get_length(self):
        return self.get_end().frames - self.get_start().frames

    def append(self, evt):
        self.events.append(evt)

    def events(self):
        return self.events

    def without_transitions(self):
        raise NotImplementedError

    def renumbered(self):
        raise NotImplementedError

    def without_timewarps(self):
        raise NotImplementedError

    def without_generators(self):
        raise NotImplementedError

    def capture_list(self):
        raise NotImplementedError

    def from_zero(self):
        raise NotImplementedError

    def spliced(self):
        raise NotImplementedError

    def to_string(self):
        """The string output of the Events, this matches a standard EDL file
        format. Using List.to_string() should return the edl back to its
        original format.
        """
        # for each Event call their to_string() method and gather the output
        output_buffer = ['TITLE: %s' % self.title, '\n']
        if self.fcm:
            output_buffer.append('FCM: %s\n' % self.fcm)
        for event in self.events:
            output_buffer.append(event.to_string())
            # output_buffer.append('')
        return ''.join(output_buffer)


class Matcher(object):
    """No documentation for this class yet.
    """

    def __init__(self, with_regex):
        self.regex = with_regex

    def matches(self, line):
        return re.match(self.regex, line)

    def apply(self, stack, line):
        sys.stderr.write("Skipping:" + line)

class FCMMatcher(Matcher):
    """Matches the FCM attribute
    """
    def __init__(self):
        Matcher.__init__(self, 'FCM: (.+)')

    def apply(self, stack, line):
        m = re.search(self.regex, line)
        try:
            stack.fcm = m.group(1).strip()
        except (IndexError, AttributeError):
            pass

class TitleMatcher(Matcher):
    """Matches the EDL Title attribute
    """
    def __init__(self):
        Matcher.__init__(self, 'TITLE: (.+)')

    def apply(self, stack, line):
        m = re.search(self.regex, line)
        try:
            stack.title = m.group(1).strip()
        except (IndexError, AttributeError):
            pass


class CommentMatcher(Matcher):
    """No documentation for this class yet.
    """

    def __init__(self):
        Matcher.__init__(self, '\*\s*(.+)')

    def apply(self, stack, line):
        #print line
        m = re.search(self.regex, line)
        if m:
            if len(stack) > 0:
                stack[-1].comments.append("* " + m.group(1))
                mo = re.search('\*\s+FROM\s+CLIP\s+NAME:\s+(.+)', line)
                if mo:
                    stack[-1].clip_name = mo.group(1).strip()


class FallbackMatcher(Matcher):
    """No documentation for this class yet.
    """

    def __init__(self):
        Matcher.__init__(self, '/^(\w)(.+)/')

    def apply(self, stack, line):
        pass


class NameMatcher(Matcher):
    """No documentation for this class yet.
    """

    def __init__(self):
        # TODO: shouldn't it be '\*\s*FROM\s+CLIP\s+NAME:(\s+)(.+)' as above,
        #       add a test for this
        Matcher.__init__(self, '\*\s*FROM CLIP NAME:(\s+)(.+)')

    def apply(self, stack, line):
        m = re.search(self.regex, line)
        #print line
        if len(stack) > 0:
            if m:
                stack[-1].clip_name = m.group(2).strip()


class SourceMatcher(Matcher):
    """No documentation for this class yet.
    """

    def __init__(self):
        Matcher.__init__(self, '\*\s*SOURCE FILE:(\s+)(.+)')

    def apply(self, stack, line):
        m = re.search(self.regex, line)
        #print line
        if len(stack) > 0:
            if m:
                stack[-1].source_file = m.group(2).strip()


class EffectMatcher(Matcher):
    """No documentation for this class yet.
    """

    def __init__(self):
        Matcher.__init__(self, 'EFFECTS NAME IS(\s+)(.+)')

    def apply(self, stack, line):
        m = re.search(self.regex, line)
        if m:
            stack[-1].transition.effect = m.group(2).strip()


class TimewarpMatcher(Matcher):
    """No documentation for this class yet.
    """

    def __init__(self, fps):
        self.fps = fps
        self.regexp = 'M2\s+(\w+)\s+(\-*\d+\.\d+)\s+(\d+:\d+:\d+[\:\;]\d+)'
        #self.regexp = 'M2\s+(\S+)\s+(\S+)\s+(\S+)'
        Matcher.__init__(self, self.regexp)

    def apply(self, stack, line):
        m = re.search(self.regexp, line)
        if m:
            stack[-1].timewarp = \
                Timewarp(m.group(1), m.group(2), m.group(3), self.fps)
            if float(m.group(2)) < 0:
                stack[-1].timewarp.reverse = True


class EventMatcher(Matcher):
    """No documentation for this class yet.
    """

    def __init__(self, fps):
        regexp = re.compile(
            r"(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S*)\s+(\d{1,2}:\d{1,2}:\d{1,2}"
            r"[:;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[:;]\d{1,3})\s+(\d{1,2}:"
            r"\d{1,2}:\d{1,2}[:;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[:;]"
            r"\d{1,3})")
        Matcher.__init__(self, regexp)
        self.fps = fps

    @classmethod
    def stripper(cls, in_string):
        return in_string.strip()

    def apply(self, stack, line):
        evt = None
        m = re.search(self.regex, line.strip())
        if m:
            matches = m.groups()
            keys = ['num', 'reel', 'track', 'tr_code', 'aux', 'src_start_tc',
                    'src_end_tc', 'rec_start_tc', 'rec_end_tc']
            values = map(self.stripper, matches)
            evt = Event(dict(zip(keys, values)))
            t = evt.tr_code
            if t == 'C':
                if len(stack) > 0:
                    stack[-1].next_event = evt
                evt.transition = Cut()
            elif t == 'D':
                evt.transition = Dissolve()
            elif re.match('W\d+', t):
                evt.transition = Wipe()
            elif t == 'K':
                evt.transition = Key()
            else:
                evt.transition = None
            evt.src_start_tc = timecode.Timecode(self.fps, evt.src_start_tc)
            evt.src_end_tc = timecode.Timecode(self.fps, evt.src_end_tc)
            evt.rec_start_tc = timecode.Timecode(self.fps, evt.rec_start_tc)
            evt.rec_end_tc = timecode.Timecode(self.fps, evt.rec_end_tc)
            stack.append(evt)
        return evt


class Effect(object):
    """No documentation for this class yet.
    """

    def __init__(self):
        pass


class Cut(Effect):
    """No documentation for this class yet.
    """

    def __init__(self):
        Effect.__init__(self)


class Wipe(Effect):
    """No documentation for this class yet.
    """

    def __init__(self):
        Effect.__init__(self)


class Dissolve(Effect):
    """No documentation for this class yet.
    """

    def __init__(self):
        Effect.__init__(self)


class Key(Effect):
    """No documentation for this class yet.
    """

    def __init__(self):
        Effect.__init__(self)


class Timewarp(object):
    """No documentation for this class yet.
    """

    def __init__(self, reel, warp_fps, tc, fps):
        self.reverse = False
        self.reel = reel
        self.fps = fps
        self.warp_fps = float(warp_fps)
        self.timecode = timecode.Timecode(fps, tc)

    def to_string(self):
        """the string representation of this Timewarp instance
        """
        return 'M2   %(reel)-8s %(warp_fps)s %(timecode)32s ' % {
            'reel': self.reel,
            'warp_fps': self.warp_fps,
            'timecode': self.timecode
        }


class Event(object):
    """Represents an edit event (or, more specifically, an EDL line denoting a
    clip being part of an EDL event)
    """

    def __init__(self, options):
        """Initialisation function with options:
        """
        self.comments = []
        self.timewarp = None
        self.next_event = None
        self.track = None
        self.clip_name = None
        self.source_file = None
        self.transition = None
        self.aux = None
        self.reel = None
        self.rec_end_tc = None
        self.rec_start_tc = None
        self.src_end_tc = None
        self.src_start_tc = None
        self.num = None
        self.tr_code = None

        # TODO: This is absolutely wrong and not safe. Please validate the
        #       incoming values, before adopting them as instance variables
        #       and instance methods
        for o in options:
            self.__dict__[o] = options[o]

    # def __repr__(self):
    #     v = ["(\n"]
    #     for k in self.__dict__:
    #         v.append("    %s=%s,\n" % (k, self.__dict__[k]))
    #     v.append(")")
    #     return ''.join(v)

    def to_string(self):
        """Human Readable string representation of edl event.

        Returns the string representation of this Event which is suitable
        to be written to a file to gather back the EDL itself.
        """
        effect = ''
        if self.transition:
            try:
                effect = 'EFFECTS NAME IS %s\n' % self.transition.effect
            except AttributeError:
                pass

        s = "%(num)-6s %(reel)-32s %(track)-5s %(tr_code)-3s %(aux)-4s " \
            "%(src_start_tc)s %(src_end_tc)s %(rec_start_tc)s " \
            "%(rec_end_tc)s\n" \
            "%(effect)s" \
            "%(notes)s" \
            "%(timewarp)s" % {
            'num': self.num if self.num else '',
            'reel': self.reel if self.reel else '',
            'track': self.track if self.track else '',
            'aux': self.aux if self.aux else '',
            'tr_code': self.tr_code if self.tr_code else '',
            'src_start_tc': self.src_start_tc,
            'src_end_tc': self.src_end_tc,
            'rec_start_tc': self.rec_start_tc,
            'rec_end_tc': self.rec_end_tc,
            'effect': effect,
            'notes': '%s\n' % '\n'.join(self.comments)
                if self.comments else '',
            'timewarp': '%s\n' % self.timewarp.to_string()
                if self.has_timewarp() else ''}

        return s

    def to_inspect(self):
        """Human Readable string representation of edl event.
        """
        return self.__repr__()

    def get_comments(self):
        """Return comments array
        """
        return self.comments

    def outgoing_transition_duration(self):
        """TBC
        """
        if self.next_event:
            return self.next_event.incoming_transition_duration()
        else:
            return 0

    def reverse(self):
        """Returns true if clip is timewarp reversed
        """
        return self.timewarp and self.timewarp.reverse

    def copy_properties_to(self, event):
        """Copy event properties to another existing event object
        """
        for k in self.__dict__:
            event.__dict__[k] = self.__dict__[k]
        return event

    def has_transition(self):
        """Returns true if clip if clip uses a transition and not a Cut
        """
        return not isinstance(self.transition, Cut)

    def incoming_transition_duration(self):
        """Returns incoming transition duration in frames, returns 0 if no
        transition set
        """
        d = 0
        if not isinstance(self.transition, Cut):
            d = int(self.aux)
        return d

    def ends_with_transition(self):
        """Returns true if the clip ends with a transition (if the next clip
        starts with a transition)
        """
        if self.next_event:
            return self.next_event.has_transition()
        else:
            return False

    def has_timewarp(self):
        """Returns true if the clip has a timewarp (speed ramp, motion memory,
        you name it)
        """
        if isinstance(self.timewarp, Timewarp):
            return True
        else:
            return False

    def black(self):
        """Returns true if event is black slug
        """
        return self.reel == "BL"

    def rec_length(self):
        """Returns record length of event in frames before transition
        """
        return self.rec_end_tc.frames - self.rec_start_tc.frames

    def rec_length_with_transition(self):
        """Returns record length of event in frames including transition
        """
        return self.rec_length() + self.outgoing_transition_duration()

    def src_length(self):
        """Returns source length of event in frames before transition
        """
        return self.src_end_tc.frames - self.src_start_tc.frames

    def capture_from_tc(self):
        raise NotImplementedError

    def capture_to_and_including_tc(self):
        raise NotImplementedError

    def capture_to_tc(self):
        raise NotImplementedError

    def speed(self):
        raise NotImplementedError

    def generator(self):
        raise NotImplementedError

    def get_clip_name(self):
        return self.clip_name

    def get_reel(self):
        return self.reel

    def event_number(self):
        return self.num

    def get_track(self):
        return self.track

    def get_tr_code(self):
        return self.tr_code

    def get_aux(self):
        return self.aux


class Parser(object):
    """No documentation for this class yet.
    """

    default_fps = "25.0"

    def __init__(self, fps=None):
        if fps is None:
            self.fps = self.default_fps
        else:
            self.fps = fps

    def get_matchers(self):
        return [TitleMatcher(), EventMatcher(self.fps), EffectMatcher(),
                NameMatcher(), SourceMatcher(), TimewarpMatcher(self.fps),
                CommentMatcher(), FCMMatcher()]

    def parse(self, input_):
        stack = None
        if isinstance(input_, str):
            input_ = input_.splitlines(True)
        if isinstance(input_, collections.Iterable):
            stack = List(self.fps)
            for l in input_:
                for m in self.get_matchers():
                    m.apply(stack, l)
        pprint.PrettyPrinter(indent=4)
        return stack
