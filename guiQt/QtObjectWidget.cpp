//
//  QtObjectWidget.cpp
//  MusicPlayer
//
//  Created by Albert Zeyer on 23.01.14.
//  Copyright (c) 2014 Albert Zeyer. All rights reserved.
//

#include "QtObjectWidget.hpp"


QtObjectWidget::QtObjectWidget(PyQtGuiObject* control) : QtBaseWidget(control) {}

/*
@implementation ObjectControlView

- (id)initWithControl:(CocoaGuiObject*)control;
{
    self = [super initWithControl:control];
    if(!self) return nil;

	control->OuterSpace = Vec(0,0);

    return self;
}

@end
*/
