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

	def __len__(self):
		return len(self.events)
		
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
		Matcher.__init__(self,'\* (.+)')

	def apply(self,stack,line):
		m=re.search(self.regex,line)
		if m:
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
			if float(m.group(2)) < 0:
				stack[-1].timewarp.reverse=True
			

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
			evt.src_start_tc=pytimecode.PyTimeCode('24',evt.src_start_tc)
			evt.src_end_tc=pytimecode.PyTimeCode('24',evt.src_end_tc)
			evt.rec_start_tc=pytimecode.PyTimeCode('24',evt.rec_start_tc)
			evt.rec_end_tc=pytimecode.PyTimeCode('24',evt.rec_end_tc)
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
		self.reverse=False
		self.reel=reel
		self.fps=float(fps)
		self.timecode=pytimecode.PyTimeCode(25)
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
		return [EventMatcher(self.fps), EffectMatcher(), NameMatcher(),
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
	p=Parser(25)
	with open('test.edl') as f:
		s=p.parse(f)
		evs=s.events
		for e in evs:
			print "Event:"+str(e.event_number())
			print " to_string                  - (ignored)"
			print " to_inspect                 - (ignored)"
			print " comments                   - "+str(e.get_comments())
			print "outgoing_transition_duration- "+str(e.outgoing_transition_duration())
			print " reverse                    - "+str(e.reverse())
			print " has_transition             - "+str(e.has_transition())
			print "incoming_transition_duration- "+str(e.incoming_transition_duration())
			print " ends_with_transition       - "+str(e.ends_with_transition())
			print " has_timewarp               - "+str(e.has_timewarp())
			print " black                      - "+str(e.black())
			print " rec_length                 - "+str(e.rec_length())
			print " rec_length_with_transition - "+str(e.rec_length_with_transition())
			print " src_length                 - "+str(e.src_length())
			print " capture_from_tc            - "+str(e.capture_from_tc())
			print " capture_to_and_including_tc- "+str(e.capture_to_and_including_tc())
			print " capture_to_tc              - "+str(e.capture_to_tc())
			print " speed                      - "+str(e.speed())
			print " generator                  - "+str(e.generator())
			print " clip_name                  - "+str(e.get_clip_name())
			print " reel                       - "+str(e.get_reel())
			print " event_number               - "+str(e.event_number())
			print " track                      - "+str(e.get_track())
			print " tr_code                    - "+str(e.get_tr_code())
			print " aux                        - "+str(e.get_aux())
