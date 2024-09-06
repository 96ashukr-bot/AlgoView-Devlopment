import React from 'react';
import { AlertCircle, Clock, Folder, Home, Star, Trash2 } from 'react-feather';

export const SideButtons = [
  {
    className: 'btn btn-primary',
    icon: <Home />,
    title: 'Home',
  },
  {
    className: 'btn btn-light',
    icon: <Folder />,
    title: 'All',
  },
  {
    className: 'btn btn-light',
    icon: <Clock />,
    title: 'Recent',
  },
  {
    className: 'btn btn-light',
    icon: <Star />,
    title: 'Starred',
  },
  {
    className: 'btn btn-light',
    icon: <AlertCircle />,
    title: 'Recovery',
  },
  {
    className: 'btn btn-light',
    icon: <Trash2 />,
    title: 'Deleted',
  },
];
