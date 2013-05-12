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
		for e in events:
			rep=rep+e.__repr__()
		rep=rep+')'
		return rep

	def append(self,evt):
		self.events.append(evt)
		
	def events(self):
		pass

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
		Matcher.__init__(self,'\* (.+)')

	def apply(self,stack,line):
		m=re.search(self.regex,line)
		if m:
			stack[-1].comments.append("* "+m.group(1))


class FallbackMatcher(Matcher):
	def __init__(self):
		Matcher.__init__(self,'/^(\w)(.+)/')	

	def apply(self,stack,line):
		pass


class NameMatcher(Matcher):
	def __init__(self):
		Matcher.__init__(self,'\* FROM CLIP NAME:(\s+)(.+)')

	def apply(self,stack,line):
		m=re.search(self.regex,line)
		if m:
			stack[-1].clip_name = m.group(2)


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
		self.regexp = 'M2\s+(\w+)\s+(\-?\d+\.\d+)\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})'
	
	def apply(self,stack,line):
		m=re.search(self.regexp,line)
		if m:
			stack[-1].timewarp = Timewarp(m.group(1),m.group(2),m.group(3))			

class EventMatcher(Matcher):
	def __init__(self,fps):
		self.fps=fps
		#self.regexp =re.compile('(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+')
		self.regexp =re.compile(r"(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w*)\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})\s+(\d{1,2}:\d{1,2}:\d{1,2}[\:\;]\d{1,3})")

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
				evt.transition=Cut()
			elif t=='D':
				evt.transition=Dissolve()
			elif re.match('W\d+',t):
				evt.transition=Wipe()
			elif t=='K':
				evt.transition=Key()
			else:
				evt.transition=None
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
	def __init__(self,reel,fps,tc):
		self.reel=reel
		self.fps=float(fps)
		self.timecode=pytimecode.PyTimeCode(25)
		self.timecode.set_timecode(tc)
	
class Event:
	"""Represents an edit event (or, more specifically, an EDL line denoting a clip being part of an EDL event)"""
	def __init__(self,options):
		"""Initialisation function with options:
		"""
		for o in options:
			self.__dict__[o]=options[o]
		self.comments=[]
		self.timewarp=None
	
	def __repr__(self):
		v="(\n"
		for k in self.__dict__:
			v=v+"    "+k+"="+str(self.__dict__[k])+",\n"
		v=v+")"
		return v
	
	def to_string(self):
		"""Human Readable string representation of edl event.
		"""
		return __repr__(self)
	
	def to_inspect(self):
		"""
			Human Readable string representation of edl event.
		"""
		x=x
	
	def comments(self):
		"""
			TBC
		"""
		return self.comments
	
	def outgoing_transition_duration(self):
		"""
			TBC
		"""
		x=x
	
	def reverse(self):
		"""
			Returns true if clip is timewarp reversed
		"""
		x=x
	
	def copy_properties_to(event):
		"""
			Copy event properties to another existing event object
		"""
		x=x
	
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
		pass
	
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
		pass
	
	def rec_length(self):
		"""
			Returns record length of event in frames before transition
		"""
		x=x
	
	def rec_length_with_transition(self):
		"""
			Returns record length of event in frames including transition
		"""
		x=x
	
	def src_length(self):
		"""
			Returns source length of event in frames before transition
		"""
		x=x
	
	def capture_from_tc(self):
		x=x
	
	def capture_to_and_including_tc(self):
		x=x
	
	def capture_to_tc(self):
		x=x
	
	def speed(self):
		x=x
	
	def generator(self):
		x=x


class Parser:
	default_fps=25.0
	def __init__(self,fps):
		if fps is None:
			self.fps=default_fps
		self.fps=fps

	def get_matchers(self):
		return [EventMatcher(self.fps), EffectMatcher(), NameMatcher(),
				TimewarpMatcher(self.fps),CommentMatcher()]
	
	def parse(self,input):
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
	p=Parser(25)
	with open('test.edl') as f:
		s=p.parse(f)