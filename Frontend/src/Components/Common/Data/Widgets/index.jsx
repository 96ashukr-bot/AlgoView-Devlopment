import React from 'react';
import { Badges, Progressbar } from '../../../../AbstractElements';
import { Database, ShoppingBag, MessageCircle, UserPlus } from 'react-feather';
import { CloudDrizzleIcon, CloudIcon, RainCloudIcon } from '../SvgIcons';


export const EmployeeStatusData = [
    {
        id:1,
        img: require('../../../../assets/images/user/4.jpg'),
        name: 'John Deo',
        status: '(14+ Online)',
        skill: 'Designer',
        exp: '2 Year',
        processbar: <Progressbar attrProgress={{ bar: true, className: 'bg-primary', value: 30 }} />
    },
    {
        id:2,
        img: require('../../../../assets/images/user/1.jpg'),
        name: 'Holio Mako',
        status: '(250+ Online)',
        skill: 'Developer',
        exp: '3 Year',
        processbar: <Progressbar attrProgress={{ bar: true, className: 'bg-secondary', value: 70 }} />
    },
    {
        id:3,
        img: require('../../../../assets/images/user/5.jpg'),
        name: 'Mohsib lara',
        status: '(99+ Online)',
        skill: 'Tester',
        exp: '5 Year',
        processbar: <Progressbar attrProgress={{ bar: true, className: 'bg-primary', value: 60 }} />
    },
    {
        id:4,
        img: require('../../../../assets/images/user/6.jpg'),
        name: 'Hileri Soli',
        status: '(150+ Online)',
        skill: 'Designer',
        exp: '3 Year',
        processbar: <Progressbar attrProgress={{ bar: true, className: 'bg-secondary', value: 30 }} />
    },
    {
        id:5,
        img: require('../../../../assets/images/user/7.jpg'),
        name: 'Pusiz bia',
        status: '(14+ Online)',
        skill: 'Designer',
        exp: '5 Year',
        processbar: <Progressbar attrProgress={{ bar: true, className: 'bg-primary', value: 90 }} />
    }
];

export const WidgetsProductData = [
    {
        id:1,
        details: 'Simply dummy text of the printing',
        quantity: 1,
        status: 'Pending',
        colorClass: 'font-primary',
        badge: <Badges attrBadge={{ className: 'badge rounded-pill pill-badge-secondary' ,color:'secondary' }}>6523</Badges>
    },
    {
        id:2,
        details: 'Long established',
        quantity: 5,
        status: 'Cancle',
        colorClass: 'font-secondary',
        badge: <Badges attrBadge={{ className: 'badge rounded-pill pill-badge-success' ,color:'success' }}>6523</Badges>
    },
    {
        id:3,
        details: 'sometimes by accident',
        quantity: 10,
        status: 'Cancle',
        colorClass: 'font-primary',
        badge: <Badges attrBadge={{ className: 'badge rounded-pill pill-badge-warning' ,color:'warning' }}>6523</Badges>
    },
    {
        id:4,
        details: 'Classical Latin literature',
        quantity: 9,
        status: 'Return',
        badge: <Badges attrBadge={{ className: 'badge rounded-pill pill-badge-primary' ,color:'primary' }}>6523</Badges>
    },
    {
        id:5,
        details: 'keep the site on the Internet',
        quantity: 8,
        status: 'Pending',
        colorClass: 'font-primary',
        badge: <Badges attrBadge={{ className: 'badge rounded-pill pill-badge-danger' ,color:'danger' }}>6523</Badges>
    },
    {
        id:6,
        details: 'Molestiae consequatur',
        quantity: 3,
        status: 'Cancle',
        colorClass: 'font-secondary',
        badge: <Badges attrBadge={{ className: 'badge rounded-pill pill-badge-info' ,color:'info' }}>6523</Badges>
    },
    {
        id:7,
        details: 'Pain can procure',
        quantity: 4,
        status: 'Return',
        colorClass: 'font-primary',
        badge: <Badges attrBadge={{ className: 'badge rounded-pill pill-badge-secondary' ,color:'primary' }}>6523</Badges>
    },
];

export const BrowserData = [
    {
        id: 1,
        img: require('../../../../assets/images/dashboard/chrome.png')
    },
    {
        id: 2,
        img: require('../../../../assets/images/dashboard/firefox.png')
    },
    {
        id: 3,
        img: require('../../../../assets/images/dashboard/safari.png')
    }
];

export const SocialData = [
    {
        id: 1,
        icon: 'fa fa-facebook',
        socialName: 'Facebook',
        count1: '6589',
        count2: '75269',
        title: 'Like'
    },
    {
        id: 2,
        icon: 'fa fa-twitter',
        socialName: 'Twitter',
        count1: '6589',
        count2: '75269',
        title: 'Follower'
    },
    {
        id: 3,
        icon: 'fa fa-linkedin',
        socialName: 'Linkedin',
        count1: '1234',
        count2: '4369',
        title: 'Linkedin'
    },
    {
        id: 4,
        icon: 'fa fa-google-plus',
        socialName: 'Google +',
        count1: '6589',
        count2: '75269',
        title: 'Like'
    }
];

export const EarningData = [
    {
        id: 1,
        classCompo: 'bg-primary',
        icon: <Database />,
        title: 'Earnings',
        count: '9856',
        iconWithClass: <Database className="icon-bg" />
    },
    {
        id: 2,
        classCompo: 'bg-secondary',
        icon: <ShoppingBag />,
        title: 'Products',
        count: '9856',
        iconWithClass: <ShoppingBag className="icon-bg" />
    },
    {
        id: 3,
        classCompo: 'bg-primary',
        icon: <MessageCircle />,
        title: 'Messages',
        count: '893',
        iconWithClass: <MessageCircle className="icon-bg" />
    },
    {
        id: 4,
        classCompo: 'bg-primary',
        icon: <UserPlus />,
        title: 'New User',
        count: '4531',
        iconWithClass: <UserPlus className="icon-bg" />
    },
];

export const RecentActivityData = [
    {
        id: 1,
        title: 'A',
        subtitle: 'Any desktop publishing.',
        date: '25 July 2022',
        time: '20 hours ago'
    },
    {
        id: 2,
        title: 'C',
        subtitle: 'Contrary to popular belief.',
        date: '25 July 2022',
        time: '20 hours ago'
    },
    {
        id: 3,
        title: 'E',
        subtitle: 'Established fact that a reader.',
        date: '25 July 2022',
        time: '20 hours ago'
    },
    {
        id: 4,
        title: 'H',
        subtitle: 'H-Code - A premium portfolio.',
        date: '25 July 2022',
        time: '20 hours ago'
    },
    {
        id: 5,
        title: 'T',
        subtitle: 'There isnt any hidden.',
        date: '25 July 2022',
        time: '20 hours ago'
    }
];

export const WeatherData = [
    {
        id: 1,
        icon: <CloudIcon />,
        temp: '25°C',
        place: 'Newyork'
    },
    {
        id: 2,
        icon: <RainCloudIcon />,
        temp: '95°C',
        place: 'Peris'
    },
    {
        id: 3,
        icon: <CloudDrizzleIcon />,
        temp: '50°C',
        place: 'India'
    }
];