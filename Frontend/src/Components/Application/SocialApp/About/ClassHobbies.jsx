import React, { Fragment } from 'react';
import { MoreVertical } from 'react-feather';
import { Card, CardBody, CardHeader, Col, Row } from 'reactstrap';
import { H5, P } from '../../../../AbstractElements';
import { Hobbies } from '../../../../Constant';

const ClassHobbies = () => {
    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <CardHeader className="social-header">
                        <H5><span>{"Hobbies and Interests"}</span><span className="pull-right"><MoreVertical /></span></H5>
                    </CardHeader>
                    <CardBody>
                        <Row className="details-about">
                            <Col sm="6">
                                <div className="your-details"><span className="f-w-600">{Hobbies}:</span>
                                    <P>{"I like to ride the bike to work, swimming, and working out. I also like reading design magazines, go to museums, and binge watching a good tv show while it’s raining outside."}</P>
                                </div>
                            </Col>
                            <Col sm="6">
                                <div className="your-details your-details-xs"><span className="f-w-600">{"Favourite Music Bands / Artists:"}</span>
                                    <P>{"Iron Maid, DC/AC, Megablow, The Ill, Kung Fighters, System of a Revenge."}</P>
                                </div>
                            </Col>
                        </Row>
                        <Row className="details-about">
                            <Col sm="6">
                                <div className="your-details"><span className="f-w-600">{"Favourite TV Shows:"}</span>
                                    <P>{"Breaking Good, RedDevil, People of Interest, The Running Dead, Found, American Guy."}</P>
                                </div>
                            </Col>
                            <Col sm="6">
                                <div className="your-details your-details-xs"><span className="f-w-600">{"Favourite Books:"}</span>
                                    <P>{"The Crime of the Century, Egiptian Mythology 101, The Scarred Wizard, Lord of the Wings, Amongst Gods, The Oracle, A Tale of Air and Water."}</P>
                                </div>
                            </Col>
                        </Row>
                        <Row className="details-about">
                            <Col sm="6">
                                <div className="your-details"><span className="f-w-600">{"Favourite Movies:"}</span>
                                    <P>{"Idiocratic, The Scarred Wizard and the Fire Crown, Crime Squad Ferrum Man."}</P>
                                </div>
                            </Col>
                            <Col sm="6">
                                <div className="your-details your-details-xs">
                                    <span className="f-w-600">{"Favourite Writers:"}</span>
                                    <P>{"Martin T. Georgeston, Jhonathan R. Token, Ivana Rowle, Alexandr Platt, Marcus Roth."}</P>
                                </div>
                            </Col>
                        </Row>
                        <Row className="details-about">
                            <Col sm="6">
                                <div className="your-details"><span className="f-w-600">{"Favourite Games:"}</span>
                                    <P>{"The First of Us, Assassin’s Squad, Dark Assylum, NMAK16, Last Cause 4, Grand Snatch Auto."}</P>
                                </div>
                            </Col>
                            <Col sm="6">
                                <div className="your-details your-details-xs"><span className="f-w-600">{"Other Interests:"}</span>
                                    <P>{"Swimming, Surfing, Scuba Diving, Anime, Photography, Tattoos, Street Art."}</P>
                                </div>
                            </Col>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default ClassHobbies;