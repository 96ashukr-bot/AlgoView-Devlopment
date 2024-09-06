import React, { Fragment } from 'react';
import { Card, Col } from 'reactstrap';
import { H6, Image, LI, P, UL } from '../../../AbstractElements';
import blog2 from '../../../assets/images/blog/blog-2.jpg';
import blog3 from '../../../assets/images/blog/blog-3.jpg';

const Perspiciatis = () => {
    return (
        <Fragment>
            <Card>
                <div className="blog-box blog-list row">
                    <Col sm="5">
                        <Image attrImage={{ className: 'img-fluid sm-100-w', src: blog2, alt: '' }} />
                    </Col>
                    <Col sm="7">
                        <div className="blog-details">
                            <div className="blog-date digits"><span>{'02'}</span> {'January 2022'}</div>
                            <H6>{'Perspiciatis unde omnis iste natus error sit voluptatem'} </H6>
                            <div className="blog-bottom-content">
                                <UL attrUL={{ className: "blog-social flex-row" }} >
                                    <LI attrLI={{ className: 'border-li' }}>{'by: Admin'}</LI>
                                    <LI attrLI={{ className: "border-li digits" }} >{'0 Hits'}</LI>
                                </UL>
                                <hr />
                                <P attrPara={{ className: 'mt-0' }} >{'inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit.'}</P>
                            </div>
                        </div>
                    </Col>
                </div>
            </Card>
            <Card>
                <div className="blog-box blog-list row">
                    <Col sm="5">
                        <Image attrImage={{ className: 'img-fluid sm-100-w', src: blog3, alt: '' }} />
                    </Col>
                    <Col sm="7">
                        <div className="blog-details">
                            <div className="blog-date digits"><span>{'03'}</span> {'January 2022'}</div>
                            <H6>{'Perspiciatis unde omnis iste natus error sit voluptatem'} </H6>
                            <div className="blog-bottom-content">
                                <UL attrUL={{ className: "blog-social flex-row" }} >
                                    <LI attrLI={{ className: 'blog-li' }}>{'by: Admin'}</LI>
                                    <LI attrLI={{ className: 'blog-li digits' }} >{'02 Hits'}</LI>
                                </UL>
                                <hr />
                                <P attrPara={{ className: 'mt-0' }} >{'inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit.'}</P>
                            </div>
                        </div>
                    </Col>
                </div>
            </Card>
        </Fragment>
    );
};

export default Perspiciatis;