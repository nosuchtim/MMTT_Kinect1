import pyffle.builtin
import time
from random import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from traceback import format_exc
from math import *
from Image import open

from pyffle.processor.default import Processor
from pyffle.builtin import *
from pyffle.util import glFreeType
from nosuch.oscutil import *

def randvertex():
	# Random points on the left half of the display
	glVertex2f(-random(),(random()*2.0 - 1.0)/2.0)

def osccallback(ev,d):
	msg = ev.oscmsg
	if len(msg) < 2:
		debug("Not enough values in oscmsg: %s"%str(msg))
		return
	if msg[0] == "/set_text":
		d.set_text(ev.oscmsg[2])
	elif msg[0] == "/set_choice":
		d.set_choice(ev.oscmsg[2],ev.oscmsg[3])
	elif msg[0] == "/attract":
		d.attract(ev.oscmsg[2])
	elif msg[0] == "/set_pos":
		d.set_pos(ev.oscmsg[2],ev.oscmsg[3])
	else:
		debug("Unrecognized osc message: %s" % str(msg))

class TextProcessor(Processor):

	def __init__(self):
		debug("TextProcessor.__init__")
		debug("getpwd=%s" % os.getcwd())
		Processor.__init__(self,passthru=False)
		otherfont = "trebucbd.ttf"
		otherfont = "arialbd.ttf"
		self.fontname = otherfont
		self.fontheight = 80
		self.smallfontname = otherfont
		self.smallfontheight = 40
		self.mediumfontname = otherfont
		self.mediumfontheight = 60
		self.bigfontname = otherfont
		self.bigfontheight = 70
		self.palettefontname = "poorich.ttf"
		self.palettefontheight = 100
		self.text = ""
		self.pos = (0,300)
		self.lastchoice0 = 0
		self.lastchoice1 = 0
		self.lastchoice2 = 0
		self.showattract = True
		self.showhints = False
		self.showbighint = False
		self.font = glFreeType.font_data(self.fontname,self.fontheight)
		self.smallfont = glFreeType.font_data(self.smallfontname,self.smallfontheight)
		self.mediumfont = glFreeType.font_data(self.mediumfontname,self.mediumfontheight)
		self.bigfont = glFreeType.font_data(self.bigfontname,self.bigfontheight)
		self.palettefont = glFreeType.font_data(self.palettefontname,self.palettefontheight)
		if not self.font or not self.smallfont:
			debug("Unable to load font %s !!" % self.fontname)
		else:
			debug("Font %s successfully initialized"%self.fontname)

		try:
			oscmon = OscMonitor("127.0.0.1",9876)
			oscmon.setcallback(osccallback,self)
		except:
			debug("Unable to start OscMonitor: %s" % format_exc())
		self.Cosine = {}
		self.Sine = {}
		for angle in range(0,361,1):
			anglerad = pi * angle / 180.0
			self.Cosine[angle] = cos(anglerad)
			self.Sine[angle] = sin(anglerad)

		self.compute_holes()

		# self.imageinit("glass.bmp")

	def imageinit(self,filename):
		self.imagefile = publicpath(filename)
		try:
			self.imageID = self.loadImage(self.imagefile)
			debug("imageID = %d" % self.imageID)

		except:
			debug("Unable to read imagefile: %s" % format_exc())

	def setupTexture(self):
		"""Render-time texture environment setup
		This method encapsulates the functions required to set up
		for textured rendering.
		"""
		# texture-mode setup, was global in original
		glEnable(GL_TEXTURE_2D)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		# glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

		# re-select our texture, could use other generated textures
		# if we had generated them earlier...
		glBindTexture(GL_TEXTURE_2D, self.imageID)   # 2d texture (x and y size)

	def __del__(self):
		debug("TextProcessor.__del__")

	def set_text(self,t):
		debug("SETTING TEXT to t=%s" % t)
		self.text = t

	def attract(self,b):
		debug("ATTRACT! b=%d" % (b))
		self.showattract = b

	def set_choice(self,t,b):
		debug("SETTING choice to t=%s b=%s" % (t,b))
		self.text = t
		self.choice = b
		if t == "":
			self.showhints = False
			self.showattract = False
			self.showbighint = False
			debug("Setting showbighint to False")
		else:
			tm = time.time()
			self.lastchoice2 = self.lastchoice1
			self.lastchoice1 = self.lastchoice0
			self.lastchoice0 = tm
			dt1 = tm - self.lastchoice1
			dt2 = tm - self.lastchoice2
			if dt1 < 5.0 and dt2 < 5.0:
				debug("Setting showhints to True!")
				self.showhints = True
			if dt1 < 2.0 and dt2 < 2.0:
				debug("Setting showbighint to True!")
				self.showbighint = True

	def set_pos(self,x,y):
		debug("SETTING POS to %f , %f" % (x,y))
		self.pos = (x,y)

	def draw(self):

		try:
			if self.showattract:
				glEnable(GL_BLEND)
				glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
				# debug("Showattract == True")
				self.draw_attract()
				return ""

			# debug("self.showattract=%d showbighint=%d text=%s" % (self.showattract,self.showbighint,self.text))

			if self.text == "":
				return ""
			glEnable(GL_BLEND)
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

			# NOTE: the return value of glPrint is the x width of the text

			if self.showbighint:
				debug("Showbighint == True")
				self.draw_bighint()
			else:
				self.draw_patchname()
				if self.choice != "":
					self.draw_holes(self.choice)
					self.draw_youhaveselected()
				# if self.showhints:
				# 	self.draw_hints()
		except:
			debug("Exception in draw!?: %s" % format_exc())
		return ""

	def draw_patchname(self):
		pos = self.pos
		glColor4f(1.0,1.0,1.0,1.0)
		self.font.glPrint(pos[0],pos[1],self.text)

	def loadImage( self, imageName ):
		"""Load an image file as a 2D texture using PIL

		This method combines all of the functionality required to
		load the image with PIL, convert it to a format compatible
		with PyOpenGL, generate the texture ID, and store the image
		data under that texture ID.

		Note: only the ID is returned, no reference to the image object
		or the string data is stored in user space, the data is only
		present within the OpenGL engine after this call exits.
		"""
		im = open(imageName)
		try:
			ix, iy, image = im.size[0], im.size[1], im.tostring("raw", "RGB", 0, -1)
			debug("Able to use tostring RGB")
		except SystemError:
			debug("Unable to use tostring RGB?")
			return -1
		# generate a texture ID
		ID = glGenTextures(1)
		# make it current
		glBindTexture(GL_TEXTURE_2D, ID)
		glPixelStorei(GL_UNPACK_ALIGNMENT,1)
		# copy the texture into the current texture ID
		debug("TEXTURE ix,iy=%f,%f" % (ix,iy))
		glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGB, GL_UNSIGNED_BYTE, image)
		# return the ID for use
		return ID

	def draw_corner(self, x, y, radius, ang0, ang1):
		x0 = x + (1.0 - self.Sine[ang0]) * radius
		y0 = y - (1.0 - self.Cosine[ang0]) * radius
		for angle in range(ang0,ang1,2):
			x1 = x + (1.0 - self.Sine[angle]) * radius
			y1 = y - (1.0 - self.Cosine[angle]) * radius
			glVertex2f(x0, y0)
			glVertex2f(x1, y1)
			x0 = x1
			y0 = y1

	def draw_hole(self, x, y, filled = False, scale=1.0):

		width = self.holew * scale
		height = self.holeh * scale
		radius = self.holer * scale

		# print("draw_hole ",x,y,width,height,radius)
		if filled:
			glBegin(GL_POLYGON)
		else:
			glBegin(GL_LINES)

		# left side
		glVertex2f(x, y+radius)
		glVertex2f(x, y+height-radius)

		# upper left corner
		self.draw_corner(x, y+height, radius, 0, 91)

		# top side
		glVertex2f(x+radius, y+height)
		glVertex2f(x+width-radius, y+height)

		# upper right corner
		self.draw_corner(x+width-2*radius, y+height, radius, 270, 361)

		# right side
		glVertex2f(x+width, y+radius)
		glVertex2f(x+width, y+height-radius)

		# lower right corner
		self.draw_corner(x+width-2*radius, y+2*radius, radius, 180, 271)

		# bottom side
		glVertex2f(x+radius, y)
		glVertex2f(x+width-radius, y)

		# lower left corner
		self.draw_corner(x, y+2*radius, radius, 90, 181)

		glEnd()  

	def draw_arrow(self,choice):
		glColor4f(0.0,1.0,0.0,0.5)
		glLineWidth(5.0)
		x0 = self.arrow[choice][0]
		y0 = self.arrow[choice][1]
		x1 = self.hole[choice][0] + (self.holew/2.0)
		y1 = self.hole[choice][1] + (self.holeh/2.0)
		glBegin(GL_LINES)
		glVertex2f(x0,y0)
		glVertex2f(x1,y1)
		glEnd()
		glColor4f(0.0,1.0,0.0,1.0)
		self.draw_hole(self.hole[choice][0]+self.holew/4.0,
				self.hole[choice][1]+self.holeh/4.0,True,0.5)

	def draw_holes(self,choice):
		glLineWidth(2.0)
		for h in self.hole:
			if choice == h:
				glColor4f(1.0,1.0,1.0,1.0)
			else:
				glColor4f(1.0,1.0,1.0,0.5)

			self.draw_hole(self.hole[h][0],self.hole[h][1],choice==h)
		self.draw_arrow(choice)

	def compute_holes(self):

		self.hole = {}
		self.arrow = {}
		left_xa = -0.725  # left-most holes
		left_xb = -0.500  # second left-most holes
		right_xa = 0.550   # right-most holes
		right_xb = 0.325  # second right-most holes

		top_ya = 0.475
		top_yb = 0.225
		bottom_ya = -0.675
		bottom_yb = -0.400

		top_yarrow = 0.08
		bottom_yarrow = -0.11

		self.holew = 0.16
		self.holeh = 0.16
		self.holer = 0.04
		########################################### UL
		self.hole["UL1"] = (left_xa,top_yb)
		self.hole["UL2"] = (left_xb,top_yb)
		self.hole["UL3"] = (left_xb,top_ya)
		self.arrow["UL1"] = (0.0,top_yarrow)
		self.arrow["UL2"] = (0.0,top_yarrow)
		self.arrow["UL3"] = (0.0,top_yarrow)
		########################################### LL
		self.hole["LL2"] = (left_xa,bottom_yb)
		self.hole["LL3"] = (left_xb,bottom_yb)
		self.hole["LL1"] = (left_xb,bottom_ya)
		self.arrow["LL2"] = (0.0,bottom_yarrow)
		self.arrow["LL3"] = (0.0,bottom_yarrow)
		self.arrow["LL1"] = (0.0,bottom_yarrow)
		########################################### UR
		self.hole["UR2"] = (right_xa,top_yb)
		self.hole["UR1"] = (right_xb,top_yb)
		self.hole["UR3"] = (right_xb,top_ya)
		self.arrow["UR2"] = (0.0,top_yarrow)
		self.arrow["UR1"] = (0.0,top_yarrow)
		self.arrow["UR3"] = (0.0,top_yarrow)
		########################################### LR
		self.hole["LR3"] = (right_xa,bottom_yb)
		self.hole["LR2"] = (right_xb,bottom_yb)
		self.hole["LR1"] = (right_xb,bottom_ya)
		self.arrow["LR3"] = (0.0,bottom_yarrow)
		self.arrow["LR2"] = (0.0,bottom_yarrow)
		self.arrow["LR1"] = (0.0,bottom_yarrow)

		debug("compute_holes is done")

	def draw_youhaveselected(self):
		glLineWidth(2.0)
		left = 410
		top = 580
		glColor4f(1.0,1.0,1.0,0.5)
		self.mediumfont.glPrint(left+45,top,"You")
		self.mediumfont.glPrint(left+32,top-60,"have")
		self.mediumfont.glPrint(left-20,top-125,"selected")

	def draw_hints(self):

		# self.draw_youhaveselected()

		glColor4f(1.0,1.0,0.0,0.7)
		low = 203
		left = 390
		self.smallfont.glPrint(left+20,low,"Wave your hands")
		self.smallfont.glPrint(left+60,low-50,"in the")
		self.smallfont.glPrint(left+40,low-100,"BIG HOLES")

	def draw_bighint(self):

		glColor4f(1.0,1.0,1.0,1.0)
		self.bigfont.glPrint(195,470,"WAVE YOUR HANDS")
		self.bigfont.glPrint(240,360,"IN THE BIG HOLES")
		left = 390
		low = 213
		# glColor4f(1.0,1.0,0.0,0.7)
		self.smallfont.glPrint(left+20,low,"SMALL holes")
		self.smallfont.glPrint(left-10,low-50,"are ONLY used to")
		self.smallfont.glPrint(left+58,low-105,"SELECT")

	def draw_attract(self):

		orig = True
		if orig:
			glColor4f(0.5,0.5,0.5,1.0)
			x = 200
			y = 435
			self.mediumfont.glPrint(x+185,y+68,"PLAY BY")
			self.mediumfont.glPrint(x,y,"W")
			self.mediumfont.glPrint(x+48,y,"A")
			self.mediumfont.glPrint(x+84,y,"VING YOUR HANDS")
			self.mediumfont.glPrint(x+70,y-65,"IN THE BIG HOLES")
			self.smallfont.glPrint(130,240,"SMALL holes are ONLY used to SELECT")
		else:
			glColor4f(0.5,0.5,0.5,1.0)
			glBegin(GL_LINE_LOOP)
			glVertex2f(-0.50, 0.37)
			glVertex2f(0.50, 0.37)
			# glVertex2f(0.55, 0.66)
			# glVertex2f(-0.55, 0.66)
			glEnd()
			x = 255
			y = 550
			self.palettefont.glPrint(x,y,"S")
			self.palettefont.glPrint(x+43,y-20,"p")
			self.palettefont.glPrint(x+92,y,"ace    alette")
			self.palettefont.glPrint(x+252,y,"P")
			x = 205
			y = 335
			self.mediumfont.glPrint(x+185,y+68,"PLAY  BY")
			self.mediumfont.glPrint(x,y,"W")
			self.mediumfont.glPrint(x+48,y,"A")
			self.mediumfont.glPrint(x+84,y,"VING  YOUR  HANDS")
			self.mediumfont.glPrint(x+70,y-65,"IN  THE  BIG  HOLES")
			# glColor4f(1.0,1.0,0.0,0.7)
			self.smallfont.glPrint(205,150,"SMALL holes are ONLY used to SELECT")
			# self.smallfont.glPrint(325,100,"HAND DEPTH MATTERS")

	def draw_bigoval(self):
		posx, posy = 0,-0.02
		sides = 32
		sz = 0.9
		# glScalef(1.0,0.61803,1.0)
		glScalef(1.0,0.96,1.0)
		glBegin(GL_LINE_LOOP)
		for i in range(sides):
			cosine=sz*cos(i*2*pi/sides)+posx
			sine=sz*sin(i*2*pi/sides)+posy
			glVertex2f(cosine,sine)
		glEnd()

