import React, { Fragment } from 'react';
import { Col, Card } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { UserProfileDesc4 } from '../../../../Constant';
import UserFooter from './Common/UserFooter';
import UserTitle from './Common/UserTitle';

const UserDetails3 = () => {
  return (
    <Fragment>
      <Col sm='12'>
        <Card>
          <div className='profile-img-style'>
            <UserTitle />
            <hr />
            <P>{UserProfileDesc4}</P>
            <UserFooter />
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};
export default UserDetails3;
