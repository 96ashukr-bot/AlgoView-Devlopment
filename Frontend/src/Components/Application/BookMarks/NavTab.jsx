import React, { Fragment, useCallback, useContext, useState } from 'react';
import { Bookmark, PlusCircle } from 'react-feather';
import { Nav, NavItem } from 'reactstrap';
import { Btn } from '../../../AbstractElements';
import { NewBookmark, Views, CreatedByMe, Favourites, SharedWithMe, MyBookmark, Tags, Newsletter, Notification, Business, Holidays, Important, Orgenization } from '../../../Constant';
import BookmarkContext from '../../../_helper/Bookmark';
import BookmarkModal from './ModalBookMark';
import ModalTag from './ModalTag';

const NavTab = () => {
  const { mybookmarkData, setActiveTabss } = useContext(BookmarkContext);
  const [addModal, setaddModal] = useState(false);
  const [tagModal, setTagModal] = useState(false);

  const activeTab = '1';

  const addToggle = () => {
    setaddModal(!addModal);
  };

  const tagToggle = () => {
    setTagModal(!tagModal);
  };
  const onHandleClick = (id) => {
    setActiveTabss(id);
  };

  const addToggleCallback = useCallback((toggle) => {
    setaddModal(toggle);
  });
  return (
    <Fragment>
      <Nav className='main-menu' role='tablist'>
        <NavItem>
          <Btn attrBtn={{ className: 'btn-mail d-block w-100 badge-light-primary', color: '', onClick: addToggle }}>
            <Bookmark className='me-2' /> {NewBookmark}
          </Btn>
          <BookmarkModal value={addModal} addToggle={addToggle} addToggleCallback={addToggleCallback} />
        </NavItem>
        <NavItem>
          <span className='main-title'>{Views}</span>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '1' ? 'active' : ''} onClick={() => onHandleClick('1')}>
            <span className='title'> {CreatedByMe}</span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '2' ? 'active' : ''} onClick={() => onHandleClick('2')}>
            <span className='title'>
              {Favourites} ({mybookmarkData.length})
            </span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '3' ? 'active' : ''} onClick={() => onHandleClick('3')}>
            <span className='title'> {SharedWithMe}</span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '4' ? 'active' : ''} onClick={() => onHandleClick('4')}>
            <span className='title'> {MyBookmark}</span>
          </a>
        </NavItem>
        <li>
          <hr />
        </li>
        <NavItem>
          <span className='main-title'>
            {Tags}
            <span className='pull-right' onClick={tagToggle}>
              <PlusCircle />
            </span>
          </span>
        </NavItem>
        <ModalTag value={tagModal} tagToggle={tagToggle} />
        <NavItem>
          <a href='#javascript' className={activeTab === '5' ? 'show' : ''} onClick={() => onHandleClick('5')}>
            <span className='title'> {Notification}</span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '6' ? 'show' : ''} onClick={() => onHandleClick('6')}>
            <span className='title'> {Newsletter}</span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '7' ? 'show' : ''} onClick={() => onHandleClick('7')}>
            <span className='title'> {Business}</span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '8' ? 'show' : ''} onClick={() => onHandleClick('8')}>
            <span className='title'> {Holidays}</span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '9' ? 'show' : ''} onClick={() => onHandleClick('9')}>
            <span className='title'> {Important}</span>
          </a>
        </NavItem>
        <NavItem>
          <a href='#javascript' className={activeTab === '10' ? 'show' : ''} onClick={() => onHandleClick('10')}>
            <span className='title'> {Orgenization}</span>
          </a>
        </NavItem>
      </Nav>
    </Fragment>
  );
};
export default NavTab;
