//
//  ClickableLabelControl.mm
//  MusicPlayer
//
//  Created by Albert Zeyer on 24.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#import "ClickableLabelControl.hpp"
#import "Builders.hpp"
#import "Threading.h"

@implementation ClickableLabelControlView
{
	NSTrackingRectTag trackingRect;
	NSColor* stdForegroundColor;
}

- (id)initWithControl:(CocoaGuiObject*)control
{
    self = [super initWithControl:control];
    if(!self) return nil;
	
	trackingRect = 0;
	PyGILState_STATE gstate = PyGILState_Ensure();
	stdForegroundColor = foregroundColor(control);
	PyGILState_Release(gstate);

    return self;
}

- (PyObject*)getTextObj
{
	CocoaGuiObject* control = [self getControl];
	PyObject* subjObj = control ? control->subjectObject : NULL;
	Py_XINCREF(subjObj);
	PyObject* textObj = NULL;
	PyObject* kws = PyDict_New();
	if(subjObj && kws) {
		PyDict_SetItemString(kws, "handleClick", Py_False);
		textObj = PyEval_CallObjectWithKeywords(subjObj, NULL, kws);
	}
	if(PyErr_Occurred()) PyErr_Print();
	Py_XDECREF(subjObj);
	Py_XDECREF(kws);
	Py_XDECREF(control);
	return textObj;
}

- (void)mouseEntered:(NSEvent *)theEvent
{
	if([self backgroundColor] == [NSColor blueColor])
		[self setTextColor:[NSColor grayColor]];
	else
		[self setTextColor:[NSColor blueColor]];
	[self setNeedsDisplay];
	[self displayIfNeeded];
}

- (void)mouseExited:(NSEvent *)theEvent
{
	[self setTextColor:stdForegroundColor];
	[self setNeedsDisplay];
	[self displayIfNeeded];
}

- (void)mouseDown:(NSEvent *)theEvent
{
	dispatch_async(getAsyncQueue(), ^{
		PyGILState_STATE gstate = PyGILState_Ensure();
		CocoaGuiObject* control = [self getControl];
		PyObject* subjObj = control ? control->subjectObject : NULL;
		Py_XINCREF(subjObj);
		PyObject* res = NULL;
		PyObject* kws = PyDict_New();
		if(subjObj && kws) {
			PyDict_SetItemString(kws, "handleClick", Py_True);
			res = PyEval_CallObjectWithKeywords(subjObj, NULL, kws);
		}
		if(PyErr_Occurred()) PyErr_Print();
		
		GuiObject* parent = control ? control->parent : NULL;
		Py_XINCREF(parent);
		if(parent && parent->meth_updateContent)
			parent->meth_updateContent(parent);
		
		Py_XDECREF(control);
		Py_XDECREF(subjObj);
		Py_XDECREF(res);
		Py_XDECREF(kws);
		Py_XDECREF(parent);
		PyGILState_Release(gstate);
	});
}

- (void)removeTrackingRect
{
	if(trackingRect) {
		[self removeTrackingRect:trackingRect];
		trackingRect = 0;
	}
}

- (void)addTrackingRect
{
	[self removeTrackingRect];
	trackingRect = [self addTrackingRect:[self bounds] owner:self userData:nil assumeInside:NO];
}

- (void)viewDidMoveToWindow
{
	[self addTrackingRect];
}

- (void)viewWillMoveToWindow:(NSWindow *)newWindow {
	[self removeTrackingRect];
}

- (void)setFrame:(NSRect)frame
{
	[super setFrame:frame];
	[self addTrackingRect];
}

- (void)setFrameSize:(NSSize)newSize
{
	[super setFrameSize:newSize];
	[self addTrackingRect];
}

- (void)setBounds:(NSRect)bounds
{
	[super setBounds:bounds];
	[self addTrackingRect];
}

@end
