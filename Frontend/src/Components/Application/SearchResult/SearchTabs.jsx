import React, { Fragment, useState } from 'react';
import { Nav, NavLink, NavItem } from 'reactstrap';

const SearchTabs = ({ callbackActive }) => {
  const [activeTab, setActiveTab] = useState('1');
  return (
    <Fragment>
      <div className='text-center'>
        <Nav tabs className='search-list' id='top-tab' role='tablist'>
          <NavItem>
            <NavLink
              className={activeTab === '1' ? 'active' : ''}
              onClick={() => {
                setActiveTab('1');
                callbackActive('1');
              }}>
              <i className='icon-target'></i>All
            </NavLink>
            <div className='material-border'></div>
          </NavItem>
          <NavItem>
            <NavLink
              className={activeTab === '2' ? 'active' : ''}
              onClick={() => {
                setActiveTab('2');
                callbackActive('2');
              }}>
              <i className='icon-image'></i>Images
            </NavLink>
            <div className='material-border'></div>
          </NavItem>
          <NavItem>
            <NavLink
              className={activeTab === '3' ? 'active' : ''}
              onClick={() => {
                setActiveTab('3');
                callbackActive('3');
              }}>
              <i className='icon-video-clapper'></i>Videos
            </NavLink>
            <div className='material-border'></div>
          </NavItem>
          <NavItem>
            <NavLink className={activeTab === '4' ? 'active' : ''}>
              <i className='icon-volume'></i>Audio
            </NavLink>
            <div className='material-border'></div>
          </NavItem>
          <NavItem className='bg-light-success'>
            <NavLink className={activeTab === '5' ? 'active' : 'txt-success'}>
              <i className='icon-map-alt'></i>Settings
            </NavLink>
            <div className='material-border'></div>
          </NavItem>
          <NavItem className='bg-light-secondary'>
            <NavLink className={activeTab === '6' ? 'active' : 'txt-secondary'}>
              <i className='icon-settings'></i>Tools
            </NavLink>
            <div className='material-border'></div>
          </NavItem>
        </Nav>
      </div>
    </Fragment>
  );
};
export default SearchTabs;
