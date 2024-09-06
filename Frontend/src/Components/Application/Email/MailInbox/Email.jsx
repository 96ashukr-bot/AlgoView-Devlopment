import React, { useEffect, Fragment, useContext, useState } from 'react';
import { UL, LI, Btn } from '../../../../AbstractElements';
import { Col, Card, CardBody, Media } from 'reactstrap';
import user from '../../../../assets/images/user/1.jpg';
import { Link } from 'react-router-dom';
import { MARKJENCO, MARKJENCOEMAIL, NEWMAIL, Inbox, AllMail, Sent, Draft, Trash, IMPORTANT, Starred, UNREAD, Spam, OUTBOX, UPDATE, ALERT, NOTES } from '../../../../Constant';
import EmailContext from '../../../../_helper/Email';
import CustomizerContext from '../../../../_helper/Customizer';

const Email = () => {
  const { allEmails, types, setType, type, getAllType, groupBy, setCompose } = useContext(EmailContext);
  const TypesOfData = types;
  const { layoutURL } = useContext(CustomizerContext);
  const [isOpen, setIsOpen] = useState(false);
  useEffect(() => {
    if (allEmails !== null) {
      const result = groupBy(allEmails, (item) => {
        return [item.type];
      });
      getAllType(result);
    }
  }, [allEmails]);

  const clickCompose = () => {
    setCompose(true);
  };

  const selectTypes = (types) => {
    setType(types);
  };

  return (
    <Fragment>
      <Col xl='3' md='6 box-col-6'>
        <div className='md-sidebar'>
          <Btn attrBtn={{ onClick: (e) => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>email filter</Btn>
          <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'} `}>
            <div className='email-left-aside'>
              <div className='email-left-aside'>
                <Card>
                  <CardBody>
                    <div className='email-app-sidebar'>
                      <Media className='align-items-center'>
                        <div className='media-size-email'>
                          <Media body className='me-3 rounded-circle img-50' src={user} alt='' />
                        </div>
                        <Media body>
                          <Link to={`/app/users/userProfile/${layoutURL}`}>
                            <h6 className='f-w-600'>{MARKJENCO}</h6>
                          </Link>
                          <p>{MARKJENCOEMAIL}</p>
                        </Media>
                      </Media>
                      <UL attrUL={{ className: 'nav main-menu flex-row', role: 'tablist' }}>
                        <LI attrLI={{ className: 'nav-item border-0' }}>
                          <Btn attrBtn={{ color: 'primary', className: 'w-100 btn-block btn-mail show', onClick: clickCompose }}>
                            <i className='icofont icofont-envelope me-2'></i>
                            {NEWMAIL}
                          </Btn>
                        </LI>
                        <LI attrLI={{ className: 'nav-item border-0', onClick: () => selectTypes('Inbox') }}>
                          <a className={`show ${type === 'Inbox' ? 'active' : ''}`} href='#javascript'>
                            <span className='title'>
                              <i className='icon-import'></i>
                              {Inbox}
                            </span>
                            <span className='badge pull-right digits'>({TypesOfData['Inbox'] ? TypesOfData['Inbox'].length : 0})</span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'nav-item border-0', onClick: () => selectTypes('AllEmails') }}>
                          <a className={`${type === 'AllEmails' ? 'active' : ''}`} href='#javascript'>
                            <span className='title'>
                              <i className='icon-folder'></i>
                              {AllMail}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0', onClick: () => selectTypes('Sent') }}>
                          <a href='#javascript' className={`${type === 'Sent' ? 'active' : ''}`}>
                            <span className='title'>
                              <i className='icon-new-window'></i>
                              {Sent}
                            </span>
                            <span className='badge pull-right digits'>({TypesOfData['Sent'] ? TypesOfData['Sent'].length : 0})</span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0', onClick: () => selectTypes('Draft') }}>
                          <a href='#javascript' className={`${type === 'Draft' ? 'active' : ''}`}>
                            <span className='title'>
                              <i className='icon-pencil-alt'></i>
                              {Draft}
                            </span>
                            <span className='badge pull-right digits'>({TypesOfData['Draft'] ? TypesOfData['Draft'].length : 0})</span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0', onClick: () => selectTypes('Trash') }}>
                          <a href='#javascript' className={`${type === 'Trash' ? 'active' : ''}`}>
                            <span className='title'>
                              <i className='icon-trash'></i>
                              {Trash}
                            </span>
                            <span className='badge pull-right digits'>({TypesOfData['Trash'] ? TypesOfData['Trash'].length : 0})</span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>
                          <a href='#javascript'>
                            <span className='title'>
                              <i className='icon-info-alt'></i>
                              {IMPORTANT}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0', onClick: () => selectTypes('favourite') }}>
                          {/* <li onClick={() => selectFev('favourite')}> */}
                          <a href='#javascript' className={`${type === 'favourite' ? 'active' : ''}`}>
                            <span className='title'>
                              <i className='icon-star'></i>
                              {Starred}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>
                          <hr />
                        </LI>
                        <LI attrLI={{ className: 'border-0', onClick: () => selectTypes('Unread') }}>
                          <a href='#javascript'>
                            <span className='title'>
                              <i className='icon-email'></i>
                              {UNREAD}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0', onClick: () => selectTypes('Spam') }}>
                          <a href='#javascript'>
                            <span className='title'>
                              <i className='icon-export'></i>
                              {Spam}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0', onClick: () => selectTypes('Outbox') }}>
                          <a href='#javascript'>
                            <span className='title'>
                              <i className='icon-share'></i>
                              {OUTBOX}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>
                          <a href='#javascript'>
                            <span className='title'>
                              <i className='icon-file'></i>
                              {UPDATE}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>
                          <a href='#javascript'>
                            <span className='title'>
                              <i className='icon-bell'></i>
                              {ALERT}
                            </span>
                          </a>
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>
                          <a href='#javascript'>
                            <span className='title'>
                              <i className='icon-notepad'></i>
                              {NOTES}
                            </span>
                            <span className='badge pull-right digits'>{'(20)'}</span>
                          </a>
                        </LI>
                      </UL>
                    </div>
                  </CardBody>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </Col>
    </Fragment>
  );
};
export default Email;
