#!/usr/bin/python
"""
	Module EDL
"""

import sys
import collections
import re
import pprint
import pytimecode

class List:
	def __init__(self,fps):
		self.events=[]
		self.fps=fps
	
	def __getitem__(self,i):
		return self.events[i]
		
	def __repr__(self):
		rep="event(\n"
		for e in self.events:
			rep=rep+e.__repr__()
		rep=rep+')'
		return rep

	def __len__(self):
		return len(self.events)
		
	def get_start(self):
		start_tc=None
		for e in self.events:
			if start_tc==None:
				start_tc=e.rec_start_tc
			else:
				if e.rec_start_tc.frames < start_tc.frames:
					start_tc=e.rec_start_tc
		return start_tc
		
	def get_end(self):
		end_tc=None
		for e in self.events:
			if end_tc==None:
				end_tc=e.rec_end_tc
			else:
				if e.rec_end_tc.frames > end_tc.frames:
					end_tc=e.rec_end_tc
		return end_tc
		
	def get_length(self):
		return self.get_end().frames-self.get_start().frames
		
	def append(self,evt):
		self.events.append(evt)
		
	def events(self):
		return self.events

	def without_transitions(self):
		pass

	def renumbered(self):
		pass

	def without_timewarps(self):
		pass

	def without_generators(self):
		pass

	def capture_list(self):
		pass

	def from_zero(self):
		pass

	def spliced(self):
		pass

class Matcher:
	def __init__(self,with_regex):
		self.regex=with_regex
	
	def matches(self,line):
		return re.match(self.regex,line)
	
	def apply(self,stack, line):
		sys.stderr.write("Skipping:"+line)

		
class CommentMatcher(Matcher):
    def __init__(self):
        Matcher.__init__(self,'\*\s*(.+)')

    def apply(self,stack,line):
        #print line
        m=re.search(self.regex,line)
        if m:
            if len(stack)>1:
                stack[-1].comments.append("* "+m.group(1))
                mo=re.search('\*\s+FROM\s+CLIP\s+NAME\:\s+(.+)',line)
                if mo:
                    stack[-1].clip_name=mo.group(1)

class FallbackMatcher(Matcher):
	def __init__(self):
		Matcher.__init__(self,'/^(\w)(.+)/')	

	def apply(self,stack,line):
		pass


class NameMatcher(Matcher):
    def __init__(self):
        Matcher.__init__(self,'\*\s*FROM CLIP NAME:(\s+)(.+)')

    def apply(self,stack,line):
        m=re.search(self.regex,line)
        #print line
        if len(stack)>0:
            if m:
                stack[-1].clip_name = m.group(2)

class SourceMatcher(Matcher):
    def __init__(self):
        Matcher.__init__(self,'\*\s*SOURCE FILE:(\s+)(.+)')

    def apply(self,stack,line):
        m=re.search(self.regex,line)
        #print line
        if len(stack)>0:
            if m:
                stack[-1].source_file = m.group(2)


class EffectMatcher(Matcher):
	def __init__(self):
		Matcher.__init__(self,'EFFECTS NAME IS(\s+)(.+)')
	
	def apply(self,stack,line):
		m=re.search(self.regex,line)
		if m:
			stack[-1].transition.effect = m.group(1)

class TimewarpMatcher(Matcher):
    def __init__(self,fps):
        self.fps=fps
        self.regexp = 'M2\s+(\w+)\s+(\-*\d+\.\d+)\s+(\d+:\d+:\d+[\:\;]\d+)'
        #self.regexp = 'M2\s+(\S+)\s+(\S+)\s+(\S+)'
        Matcher.__init__(self,self.regexp)

    def apply(self,stack,line):
        m=re.search(self.regexp,line)
        if m:
            stack[-1].timewarp = Timewarp(m.group(1),m.group(2),m.group(3),self.fps)
            if float(m.group(2)) < 0:
                stack[-1].timewarp.reverse=True
			

class EventMatcher(Matcher):
    def __init__(self,fps):
        self.fps=fps
        #self.regexp =re.compile('(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+')
        self.regexp =re.compile(r"(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S*)\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})")

    def stripper(self,instring):
        return instring.strip()

    def apply(self,stack,line):
        evt=None
        m=re.search(self.regexp,line.strip())
        if m:
            matches=m.groups()
            keys = ['num','reel','track','tr_code','aux','src_start_tc','src_end_tc','rec_start_tc','rec_end_tc']
            values = map(self.stripper,matches)
            evt = Event(dict(zip(keys,values)))
            t=evt.tr_code
            if t=='C':
                if len(stack) > 0:
                    stack[-1].next_event=evt
                evt.transition=Cut()
            elif t=='D':
                evt.transition=Dissolve()
            elif re.match('W\d+',t):
                evt.transition=Wipe()
            elif t=='K':
                evt.transition=Key()
            else:
                evt.transition=None
            evt.src_start_tc=pytimecode.PyTimeCode(self.fps,evt.src_start_tc)
            evt.src_end_tc=pytimecode.PyTimeCode(self.fps,evt.src_end_tc)
            evt.rec_start_tc=pytimecode.PyTimeCode(self.fps,evt.rec_start_tc)
            evt.rec_end_tc=pytimecode.PyTimeCode(self.fps,evt.rec_end_tc)
            stack.append(evt)
        return evt

class Effect:
	def __init__(self):
		pass

class Cut(Effect):
	def __init__(self):
		Effect.__init__(self)
		
		
class Wipe(Effect):
	def __init__(self):
		Effect.__init__(self)
		
		
class Dissolve(Effect):
	def __init__(self):
		Effect.__init__(self)

class Key(Effect):
	def __init__(self):
		Effect.__init__(self)

class Timewarp:
    def __init__(self,reel,warp_fps,tc,fps):
        self.reverse=False
        self.reel=reel
        self.fps=fps
        self.warp_fps=float(warp_fps)
        self.timecode=pytimecode.PyTimeCode(fps)
        self.timecode.set_timecode(tc)

class Event:
	"""Represents an edit event (or, more specifically, an EDL line denoting a clip being part of an EDL event)"""
	def __init__(self,options):
		"""Initialisation function with options:
		"""
		self.comments=[]
		self.timewarp=None
		self.next_event=None
		self.track=None
		self.clip_name=None
		self.source_file=None
		for o in options:
			self.__dict__[o]=options[o]
	
	def __repr__(self):
		v="(\n"
		for k in self.__dict__:
			v=v+"    "+k+"="+str(self.__dict__[k])+",\n"
		v=v+")"
		return v
	
	def to_string(self):
		"""Human Readable string representation of edl event.
		"""
		return self.__repr__()
	
	def to_inspect(self):
		"""
			Human Readable string representation of edl event.
		"""
		return self.__repr__()
	
	def get_comments(self):
		"""
			Return comments array
		"""
		return self.comments
	
	def outgoing_transition_duration(self):
		"""
			TBC
		"""
		if self.next_event:
			return self.next_event.incoming_transition_duration()
		else:
			return 0

	def reverse(self):
		"""
			Returns true if clip is timewarp reversed
		"""
		return (self.timewarp and self.timewarp.reverse)
	
	def copy_properties_to(event):
		"""
			Copy event properties to another existing event object
		"""
		for k in self.__dict__:
			event.__dict__[k]=self.__dict__[k]
		return event
		
	def has_transition(self):
		"""
			Returns true if clip if clip uses a transition and not a Cut
		"""
		return not isinstance(self.transition,Cut)
	
	def incoming_transition_duration(self):
		"""
			Returns incoming transition duration in frames, returns 0 if no transition set 
		"""
		d=0
		if not isinstance(self.transition,Cut):
			d=int(self.aux)
		return d
	
	def ends_with_transition(self):
		"""
			Returns true if the clip ends with a transition (if the next clip starts with a transition)
		"""
		if self.next_event:
			return self.next_event.has_transition()
		else:
			return False
	
	def has_timewarp(self):
		"""
			Returns true if the clip has a timewarp (speed ramp, motion memory, you name it)
		"""
		if isinstance(self.timewarp,Timewarp):
			return True
		else:
			return False
	
	def black(self):
		""" 
			Returns true if event is black slug
		"""
		return self.reel=="BL"
	
	def rec_length(self):
		"""
			Returns record length of event in frames before transition
		"""
		return self.rec_end_tc.frames-self.rec_start_tc.frames
	
	def rec_length_with_transition(self):
		"""
			Returns record length of event in frames including transition
		"""
		return self.rec_length()+self.outgoing_transition_duration()
	
	def src_length(self):
		"""
			Returns source length of event in frames before transition
		"""
		return self.src_end_tc.frames-self.src_start_tc.frames
	
	def capture_from_tc(self):
		print "Not yet implemented"
	
	def capture_to_and_including_tc(self):
		print "Not yet implemented"
	
	def capture_to_tc(self):
		print "Not yet implemented"
	
	def speed(self):
		print "Not yet implemented"
	
	def generator(self):
		print "Not yet implemented"
		
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

class Parser:
	default_fps=25.0
	def __init__(self,fps):
		if fps is None:
			self.fps=default_fps
		self.fps=fps

	def get_matchers(self):
		return [EventMatcher(self.fps), EffectMatcher(), NameMatcher(), SourceMatcher(),
				TimewarpMatcher(self.fps),CommentMatcher()]
	
	def parse(self,input):
		stack=None
		if isinstance(input,str):
			input=input.splitlines(True)
		if isinstance(input,collections.Iterable):
			stack=List(self.fps)
			for l in input:
				for m in self.get_matchers():
					m.apply(stack,l)
		pp=pprint.PrettyPrinter(indent=4)
		#pp.pprint(stack.events)
		return stack
		
if __name__ == '__main__':
	pass
