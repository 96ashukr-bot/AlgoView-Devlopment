import React, { Fragment } from 'react';
import blogSingle from '../../assets/images/blog/blog-single.jpg';
import { Container, Row, Col, Media, Card, CardBody } from 'reactstrap';
import { Comment } from '../../Constant';
import { Breadcrumbs, H4, LI, P, UL } from '../../AbstractElements';
import { BlogSingleData } from '../Common/Data/Blog';
import CommonContain from './CommonContain';

const BlogSingle = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Blog Single' parent='Blog' title='Blog Single' />
      <Container fluid={true}>
        <Row>
          <Col sm='12'>
            <div className='blog-single'>
              <div className='blog-box blog-details'>
                <Media className='img-fluid w-100' src={blogSingle} alt='blog-main' />
                <Card>
                  <CardBody>
                    <div className='blog-details'>
                      <UL attrUL={{ className: 'blog-social flex-row simple-list' }}>
                        <LI attrLI={{ className: 'digits border-0' }}>{'25 July 2022'}</LI>
                        <LI attrLI={{ className: 'border-0' }}>
                          <i className='icofont icofont-user'></i>
                          {'Mark'} <span>{'Jecno'} </span>
                        </LI>
                        <LI attrLI={{ className: 'digits border-0' }}>
                          <i className='icofont icofont-thumbs-up'></i>
                          {'02'}
                          <span>{'Hits'}</span>
                        </LI>
                        <LI attrLI={{ className: 'digits border-0' }}>
                          <i className='icofont icofont-ui-chat'></i>
                          {'598 Comments'}
                        </LI>
                      </UL>
                      <H4>{'Vibrant horizontal stripes pattern cool soft cotton fabric front zipper snuggly jersey-lined hood robust cuffs and twin pockets.'}</H4>
                      <div className='single-blog-content-top'>
                        <P>
                          {
                            "Effortless comfortable full leather lining eye-catching unique detail to the toe low 'cut-away' sides clean and sleek. Stripe shirts plain button-down collar short-sleeved three-color button navy top-fused collar. Tops shift shape rich fabric relaxed fitting size true black gold zip virgin wool. Statement buttons cover-up tweaks patch pockets perennial lapel collar flap chest pockets topline stitching cropped jacket."
                          }
                        </P>
                        <P>
                          {
                            "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English. Many desktop publishing packages and web page editors now use Lorem Ipsum as their default model text, and a search for 'lorem ipsum' will uncover many web sites still in their infancy. Various versions have evolved over the years, sometimes by accident, sometimes on purpose (injected humour and the like"
                          }
                        </P>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              </div>
              <Card className='comment-box'>
                <CardBody>
                  <H4>{Comment}</H4>
                  <UL>
                    {BlogSingleData.map((item) => (
                      <LI attrLI={{ className: 'border-0' }} key={item.id}>
                        {item.id !== 2 ? (
                          <CommonContain item={item} />
                        ) : (
                          <UL>
                            <LI>
                              <CommonContain item={item} />
                            </LI>
                          </UL>
                        )}
                      </LI>
                    ))}
                  </UL>
                </CardBody>
              </Card>
            </div>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default BlogSingle;
