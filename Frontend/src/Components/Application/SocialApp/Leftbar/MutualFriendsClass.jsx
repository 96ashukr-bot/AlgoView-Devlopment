import React, { Fragment, useState } from 'react';
import { Card, CardHeader, CardBody, Media, Form, FormGroup, Input, Collapse } from 'reactstrap';
import { MutualFriends } from '../../../../Constant';
import { Btn, H5, Image } from '../../../../AbstractElements';
import { MutualFriendsData } from '../../../../Data/SocialHeader';
import { ChevronDown, ChevronUp } from 'react-feather';

const MutualFriendsClass = () => {
  const [isMutual, setisMutual] = useState(true);
  return (
    <Fragment>
      <Card>
        <CardHeader>
          <H5 attrH5={{ className: 'mb-0' }}>
            <Btn attrBtn={{ className: 'd-flex justify-content-between', color: 'link', onClick: () => setisMutual(!isMutual) }}>
              {MutualFriends}
              {isMutual ? <ChevronUp className='m-0' /> : <ChevronDown className='m-0' />}
            </Btn>
          </H5>
        </CardHeader>
        <Collapse isOpen={isMutual}>
          <CardBody className='social-status filter-cards-view'>
            <Form>
              <FormGroup>
                <Input className='form-control-social' type='search' placeholder='Search Contacts..' />
              </FormGroup>
            </Form>
            {MutualFriendsData.map((data, i) => (
              <Media key={i}>
                <Image attrImage={{ className: 'img-50 rounded-circle m-r-15 mb-0', src: `${data.img}`, alt: 'twoImg' }} />
                <div className={`social-status ${data.status}`}></div>
                <Media body>
                  <span className='f-w-500 d-block'>{data.name}</span>
                  <span className='d-block'>{data.email}</span>
                </Media>
              </Media>
            ))}
          </CardBody>
        </Collapse>
      </Card>
    </Fragment>
  );
};

export default MutualFriendsClass;
