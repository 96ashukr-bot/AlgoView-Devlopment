import React, { Fragment, useEffect, useState } from 'react';
import { Archive, ArrowRight, FileText } from 'react-feather';
import errorImg from '../../../assets/images/search-not-found.png';
import { H5, H6, Image, LI, UL } from '../../../AbstractElements';
import { BrowseArticles } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';
import { Card, CardBody, Col, Row } from 'reactstrap';
import axios from 'axios';
import { KnowledgebaseApi } from '../../../api';

const BrowseArticlesClass = () => {
    const [search, setsearch] = useState([]);

    useEffect(() => {
        axios.get(KnowledgebaseApi).then(res => setsearch(res.data))
    }, [])


    return (
        <Fragment>
            <Col sm="12">
                <Row >
                    <Col sm="12">
                        <div className="header-faq">
                            <H5 attrH5={{ className: "mb-0" }} >{"Browse articles by category"}</H5>
                        </div>
                    </Col>
                    <Col sm="12">
                        <Card>
                            <HeaderCard title={BrowseArticles} />
                            <CardBody>
                                <Row  className="browse g-sm-4 g-3">
                                    {search.length > 0 ? search.map((data, i) => {
                                        return (
                                            <Col xl="4 xl-50" md="6" key={i}>
                                                <div className="browse-articles browse-bottom">
                                                    <H6>
                                                        <span><Archive /></span>{data.inspantitle}{data.title}
                                                    </H6>
                                                    <UL>
                                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><span>{data.text1}</span><span className='badge bg-primary pull-right'>{data.text1_badge}</span></a></LI>
                                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><span>{data.text2}</span><span className='badge bg-primary pull-right'>{data.text2_badge}</span></a></LI>
                                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><span>{data.text3}</span><span className='badge bg-primary pull-right'>{data.text3_badge}</span></a></LI>
                                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><span>{data.text4}</span><span className='badge bg-primary pull-right'>{data.text4_badge}</span></a></LI>
                                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><ArrowRight /></span><span>{data.text5}</span></a></LI>
                                                    </UL>
                                                </div>
                                            </Col>

                                        )

                                    }) :
                                        <Image attrImage={{ className: "img-fluid m-auto", src: `${errorImg}`, alt: "" }} />
                                    }
                                </Row>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Col>
        </Fragment>
    )
}

export default BrowseArticlesClass;