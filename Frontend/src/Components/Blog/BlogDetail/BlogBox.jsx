import React, { Fragment } from 'react';
import { Card, Col } from 'reactstrap';
import { P, Image, H4, UL, LI } from '../../../AbstractElements';
import { MarkJecno } from '../../../Constant';
import blog from '../../../assets/images/blog/blog.jpg';

const BlogBox = () => {
  return (
    <Fragment>
      <Col xl='6' className='set-col-12 box-col-12'>
        <Card>
          <div className='blog-box blog-shadow'>
            <Image attrImage={{ className: 'img-fluid', src: blog, alt: '' }} />
            <div className='blog-details'>
              <P attrPara={{ className: 'digits' }}>{'25 July 2022'}</P>
              <H4>{'Accusamus et iusto odio dignissimos ducimus qui blanditiis.'}</H4>
              <UL attrUL={{ className: 'blog-social flex-row' }}>
                <LI attrLI={{ className: 'blog-li ' }}>
                  <i className='icofont icofont-user'></i>
                  {MarkJecno}
                </LI>
                <LI attrLI={{ className: 'blog-li digits ' }}>
                  <i className='icofont icofont-thumbs-up'></i>
                  {'02 Hits'}
                </LI>
                <LI attrLI={{ className: 'blog-li digits ' }}>
                  <i className='icofont icofont-ui-chat'></i>
                  {'598 Comments'}
                </LI>
              </UL>
            </div>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default BlogBox;
