import React, { Fragment } from 'react';
import { VerticalTimeline, VerticalTimelineElement } from 'react-vertical-timeline-component';
import { Edit, Video, Activity,  PlayCircle } from 'react-feather';
import { H4, Image, P,Breadcrumbs } from '../../../AbstractElements';
import { Card, CardBody, CardHeader } from 'reactstrap';


const Timeline1 = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Timeline" parent="Bonus Ui" title="Timeline" />
            <Card>
                <CardHeader>
                    <h5> Timeline </h5>
                </CardHeader>
                <CardBody>
                    <VerticalTimeline>
                        <VerticalTimelineElement
                            className="vertical-timeline-element--work"
                            animate={true}
                            date="Jan 14"
                            icon={<Edit />}>
                            <H4 attrH4={{ className: 'vertical-timeline-element-subtitle' }}>{'Title of section 1'}</H4>
                            <P>
                                {'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Iusto, optio, dolorum provident rerum aut hic quasi placeat iure tempora laudantium ipsa ad debitis unde? Iste voluptatibus minus veritatis qui ut.'}
                            </P>
                        </VerticalTimelineElement>
                        <VerticalTimelineElement
                            className="vertical-timeline-element--work"
                            date="Jan 18"
                            icon={<Video />}>
                            <H4 attrH4={{ className: 'vertical-timeline-element-subtitle' }} >{'Title of section 2'}</H4>
                            <div className="ratio ratio-21x9 m-t-20">
                                <iframe src="https://www.youtube.com/embed/wpmHZspl4EM" allowFullScreen title="myFrame"></iframe>
                            </div>
                        </VerticalTimelineElement>
                        <VerticalTimelineElement
                            className="vertical-timeline-element--work"
                            date="Jan 24"
                            animate={true}
                            icon={<PlayCircle />}>
                            <H4 attrH4={{ className: 'vertical-timeline-element-subtitle' }} >{'Title of section 3'}</H4>
                            <Image attrImage={{ className: 'img-fluid p-t-20', src: `${require('../../../assets/images/banner/1.jpg')}`, alt: 'timelineImg1' }} />
                        </VerticalTimelineElement>
                        <VerticalTimelineElement
                            className="vertical-timeline-element--work"
                            date="Feb 14"
                            animate={true}
                            icon={<Activity />}>
                            <H4 attrH4={{ className: 'vertical-timeline-element-subtitle' }} >{'Title of section 4'}</H4>
                            <audio controls preload="none">
                                <source src={require('../../../assets/audio/horse.ogg')} type="audio/ogg" />
                                {'Your browser does not support the audio element.'}
                            </audio>
                        </VerticalTimelineElement>
                        <VerticalTimelineElement
                            className="vertical-timeline-element--education"
                            date="Feb 18"
                            animate={true}
                            icon={<PlayCircle />}>
                            <H4 attrH4={{ className: 'vertical-timeline-element-subtitle' }} >{'Title of section 5'}</H4>
                            <Image attrImage={{ className: 'img-fluid p-t-20', src: `${require('../../../assets/images/banner/3.jpg')}`, alt: 'timelineImg2' }} />
                        </VerticalTimelineElement>
                        <VerticalTimelineElement
                            className="vertical-timeline-element--education"
                            date="Feb 26"
                            animate={true}
                            icon={<Edit />}>
                            <H4 attrH4={{ className: 'vertical-timeline-element-subtitle' }} >{'Final Section'}</H4>
                            <P>
                                {'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Iusto, optio, dolorum provident'}
                                {'rerum aut hic quasi placeat iure tempora laudantium ipsa ad debitis unde? Iste voluptatibus minus'}
                                {'veritatis qui ut.'}
                            </P>
                        </VerticalTimelineElement>
                    </VerticalTimeline>
                </CardBody>
            </Card>
        </Fragment>
    );
};

export default Timeline1;