import { Activity, Cast, CheckCircle, FilePlus, Trash } from 'react-feather';

export const TodoCategoriesList = [
  {
    title: 'All Task',
    icon: <FilePlus />,
    color: 'primary',
  },
  {
    title: 'Completed',
    icon: <CheckCircle />,
    badge: '3',
    color: 'success',
  },
  {
    title: 'Pending',
    icon: <Cast />,
    badge: '2',
    color: 'danger',
  },
  {
    title: 'In Process',
    icon: <Activity />,
    badge: '2',
    color: 'info',
    badgeColor: 'primary',
  },
  {
    title: 'Trash',
    icon: <Trash />,
    color: 'danger',
  },
];
