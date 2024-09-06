import React, { Fragment, useCallback, useContext, useState } from 'react';
import { Card, Col, Row } from 'reactstrap';
import EmailContext from '../../../../_helper/Email';
import EmailTopToggle from './EmailTop';
import EmptyClass from './EmptyMail';
import AllEmailsClass from './AllEmailClass';
import MailContain from './MailContain';

const MailSidebar = () => {
  const { types, allEmails, type, setCompose, getAllEmailsAsyn, getAllType, groupBy, setSingleMailRecord } = useContext(EmailContext);
  const [emailIds, setEmailIds] = useState([]);
  const [checked, setchecked] = useState(false);
  const mailData = [];
  const TypesOfData = types;

  const selectedFav = false;

  const selectedCompose = (email) => {
    setCompose(false);
    setSingleMailRecord(email);
  };

  const selectedmail = (e, emailID) => {
    const IDs = emailIds;
    setchecked(e.target.checked);
    if (emailIds == null) {
      setEmailIds(mailData);
    } else {
      if (e.target.checked) {
        IDs.push(emailID);
        setEmailIds(IDs);
        const arr = [...new Set(emailIds)];
        setEmailIds(arr);
      } else {
        setEmailIds(mailData);
      }
    }
  };

  const moreCallBack = useCallback((typeSelected) => {
    moveEmails(typeSelected);
  });

  const moveEmails = (val) => {
    [...document.querySelectorAll('.checkbox_animated')].map((input) => {
      if (input.checked) {
        let fakeInput = {
          target: {
            value: input.value,
            checked: false,
          },
        };
        input.checked = !input.checked;
        selectedmail(fakeInput);
      }
      return null;
    });
    for (var i = 0; i < allEmails.length; i++) {
      if (emailIds.includes(allEmails[i].id)) {
        allEmails[i].type = val;
      }
    }

    var result = groupBy(allEmails, function (item) {
      return [item.type];
    });

    getAllEmailsAsyn(allEmails);
    getAllType(result);
  };

  const selectedmailCallback = useCallback((e, emailID) => {
    selectedmail(e, emailID);
  });

  const selectMailCallback = useCallback((val) => {
    selectedCompose(val);
  });

  return (
    <Fragment>
      <Col xl='9' className='box-col-6'>
        <div className='email-right-aside email-page'>
          <Card className='email-body'>
            <Row>
              <Col xl='4' md='12' className='box-md-12 pr-0'>
                <div className='pe-0 b-r-light'></div>
                <EmailTopToggle selectedFav={selectedFav} moreCallBack={moreCallBack} emailIds={emailIds} />
                <div className='inbox custom-scrollbar'>
                  {selectedFav ? (
                    allEmails.filter((email) => email.favourite === true).length > 0 ? (
                      allEmails
                        .filter((email) => email.favourite === true)
                        .map((list, index) => {
                          return <AllEmailsClass list={list} selectMailCallback={selectMailCallback} selectedmailCallback={selectedmailCallback} key={index} checked={checked} />;
                        })
                    ) : (
                      <EmptyClass />
                    )
                  ) : TypesOfData[type] ? (
                    TypesOfData[type].map((list, index) => {
                      return <AllEmailsClass list={list} selectMailCallback={selectMailCallback} selectedmailCallback={selectedmailCallback} key={index} checked={checked} />;
                    })
                  ) : type === 'AllEmails' ? (
                    allEmails.map((list, index) => {
                      return <AllEmailsClass list={list} selectMailCallback={selectMailCallback} selectedmailCallback={selectedmailCallback} key={index} checked={checked} />;
                    })
                  ) : (
                    <EmptyClass />
                  )}
                </div>
              </Col>
              <MailContain />
            </Row>
          </Card>
        </div>
      </Col>
    </Fragment>
  );
};
export default MailSidebar;
