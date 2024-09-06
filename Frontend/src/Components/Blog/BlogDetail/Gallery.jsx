import React, { Fragment } from 'react';
import { Card, Col } from 'reactstrap';
import { H6, Image, LI, UL } from '../../../AbstractElements';
import { BlogData } from '../../Common/Data/Blog';

const Gallery = () => {
  return (
    <Fragment>
      {BlogData.map((item) => (
        <Col md='6' xxl='3' className='box-col-6' key={item.id}>
          <Card>
            <div className='blog-box blog-grid text-center'>
              <Image attrImage={{ className: 'img-fluid top-radius-blog', src: `${require(`../../../assets/images/${item.img}`)}`, alt: '' }} />
              <div className='blog-details-main'>
                <UL attrUL={{ className: 'blog-social flex-row' }}>
                  <LI attrLI={{ className: 'digits' }}>{item.date}</LI>
                  <LI attrLI={{ className: 'digits' }}>{item.admin}</LI>
                  <LI attrLI={{ className: 'digits' }}>{item.hits}</LI>
                </UL>
                <hr />
                <H6 attrH6={{ className: 'blog-bottom-details' }}>{item.details}</H6>
              </div>
            </div>
          </Card>
        </Col>
      ))}
    </Fragment>
  );
};

export default Gallery;
