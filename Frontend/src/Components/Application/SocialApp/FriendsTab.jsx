import React, { Fragment, useState, useEffect } from 'react';
import { Row, Col, Card, CardBody } from 'reactstrap';
import axios from 'axios';

import { Link } from 'react-router-dom';
import { H5, Image } from '../../../AbstractElements';
import { UserCardApi } from '../../../api';
import SvgIcon from '../../Common/Component/SvgIcon';
import SocialLinks from '../Users/UsersCards/SocialLinks';
import SocialData from '../Users/UsersCards/SocialData';

const FriendsTab = () => {
  const [cards, setCards] = useState([]);

  useEffect(() => {
    axios.get(UserCardApi).then((res) => setCards(res.data));
  }, []);

  return (
    <Fragment>
      <Row>
        {cards.map((item) => {
          return (
            <Col key={item.id} xxl='3' xl='4' sm='6' className='col-ed-4 box-col-4'>
              <Card className='social-profile'>
                <CardBody>
                  <div className='social-img-wrap'>
                    <div className='social-img'>
                      <Image attrImage={{ src: require(`../../../assets/images/${item.avatar}`), alt: 'profile' }} />
                    </div>
                    <div className='edit-icon'>
                      <SvgIcon iconId={item.icon} />
                    </div>
                  </div>
                  <div className='social-details'>
                    <H5 attrH5={{ className: 'mb-1' }}>
                      <Link to={`/app/social-app`}>{item.name}</Link>
                    </H5>
                    <span className='f-light'>{item.email}</span>
                    <SocialLinks />
                    <SocialData totalPost={item.totalPost} follower={item.follower} following={item.following} />
                  </div>
                </CardBody>
              </Card>
            </Col>
          );
        })}
      </Row>
    </Fragment>
  );
};

export default FriendsTab;
