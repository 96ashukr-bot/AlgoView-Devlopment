import React, { Fragment } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import HeaderCard from '../../../Common/Component/HeaderCard';
import { ActivityLog } from '../../../../Constant';
import { H6, P } from '../../../../AbstractElements';
import { MessageSquare, ThumbsUp, UserPlus } from 'react-feather';

const ActivityLogClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title={ActivityLog} />
                    <CardBody>
                        <div className="activity-log">
                            <div className="my-activity">
                                <H6 attrH6={{ className: "f-w-600 mb-3" }} >{"Today"}</H6>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Comeren Diaz likes your photos."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Karlene Lex and Comeren Diaz now friends."}</P>
                                <P><span><MessageSquare className="m-r-20" /></span>{"Sarah Loren wrote on your timeline"}</P>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Johny Waston likes your post's."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Andew Jon became friends with Comeren Diaz."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Johny Waston became friends with Bucky Barnes."}</P>
                            </div>
                            <div className="my-activity">
                                <H6 attrH6={{ className: "f-w-600 mb-3" }} >{"25 December"}</H6>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Comeren Diaz likes your photos."}</P>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Johny Waston likes your post's."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Karlene Lex and Comeren Diaz now friends."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Johny Waston became friends with Bucky Barnes."}</P>
                                <P><span><MessageSquare className="m-r-20" /></span>{"Sarah Loren wrote on your timeline"}</P>
                                <P><span><MessageSquare className="m-r-20" /></span>{"Comeren Diaz wrote on your timeline"}</P>
                            </div>
                            <div className="my-activity">
                                <H6 attrH6={{ className: "f-w-600 mb-3" }} >{"8 september"}</H6>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Comeren Diaz likes your photos."}</P>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Johny Waston likes your post's."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Karlene Lex and Comeren Diaz now friends."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Johny Waston became friends with Bucky Barnes."}</P>
                                <P><span><MessageSquare className="m-r-20" /></span>{"Sarah Loren wrote on your timeline"}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Andew Jon became friends with Comeren Diaz."}</P>
                            </div>
                            <div className="my-activity">
                                <H6 attrH6={{ className: "f-w-600 mb-3" }} >{"6 June"}</H6>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Comeren Diaz likes your photos."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Karlene Lex and Comeren Diaz now friends."}</P>
                                <P><span><MessageSquare className="m-r-20" /></span>{"Sarah Loren wrote on your timeline"}</P>
                                <P><span><ThumbsUp className="m-r-20" /></span>{"Johny Waston likes your post's."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Andew Jon became friends with Comeren Diaz."}</P>
                                <P><span><UserPlus className="m-r-20" /></span>{"Johny Waston became friends with Bucky Barnes."}</P>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default ActivityLogClass;