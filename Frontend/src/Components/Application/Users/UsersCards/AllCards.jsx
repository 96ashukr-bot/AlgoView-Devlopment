import React, { Fragment, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardBody,Col } from 'reactstrap';
import {  H5, Image } from '../../../../AbstractElements';
import { UserCardApi } from '../../../../api';

import axios from 'axios';
import SvgIcon from '../../../Common/Component/SvgIcon';
import SocialLinks from './SocialLinks';
import SocialData from './SocialData';
const AllCards = () => {
  const [cards, setCards] = useState([]);

  useEffect(() => {
    const ac = new AbortController();
    axios.get(UserCardApi).then((res) => setCards(res.data));
    return () => ac.abort();
  }, []);

  return (
    <Fragment>
      {cards.map((item) => {
        return (
          <Col key={item.id} xl='4' sm='6' xxl='3' className='col-ed-4 box-col-4'>
            <Card className='social-profile'>
              <CardBody>
                <div className='social-img-wrap'>
                  <div className='social-img'>
                    <Image attrImage={{ src: require(`../../../../assets/images/${item.avatar}`), alt: 'profile' }} />
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
    </Fragment>
  );
};
export default AllCards;
