import { H6, P, UL, LI, Btn } from '../../../../AbstractElements';
import React, { Fragment } from 'react';

const JobDescription = () => {
    return (
        <Fragment>
            <div className="job-description">
                <H6>Job Description</H6>
                <P attrPara={{ className: 'text-start' }} >We are looking for a UI/UX Designer to join our team. The world is seeing an explosion in the amount and variety of location-baWe are looking for a versatile UX/UI Designer to join our growing design team. Our designers contribute to clients’ projects at all stages of development. We might start from scratch, conducting user and stakeholder interviews, making personas and journey maps, and continue on to iterating on designs and prototypes through delivering final assets for launch. We might come into the middle of an in-flight program-size project and conduct analysis and usability correction or feature enhancement. We might provide research and vision for handoff to an internal development team.</P>
                {/* <!-- <p>Front-end web designers combine design, programming, writing and organizational skills in their work. They help shape the vision for a company's online content.</p>--> */}
            </div>
            <div className="job-description">
                <H6>Qualifications </H6>
                <UL>
                    <LI attrLI={{ className: 'border-0' }}>Have shipped multiple iOS, Android, and/or web products </LI>
                    <LI attrLI={{ className: 'border-0' }}>5+ years UI/UX experience</LI>
                    <LI attrLI={{ className: 'border-0' }}>Portfolio demonstrating mastery of native iOS, Android, and/or responsive web design principles</LI>
                    <LI attrLI={{ className: 'border-0' }}>Ability to autonomously pursue elegant solutions to open-ended problems</LI>
                    <LI attrLI={{ className: 'border-0' }}>Comfort with ambiguity</LI>
                    <LI attrLI={{ className: 'border-0' }}>ively work on more than one project at a time</LI>
                    <LI attrLI={{ className: 'border-0' }}>Experience conducting user research and stakeholder interviews</LI>
                    <LI attrLI={{ className: 'border-0' }}>Solid grasp of standard design tools, ex: Sketch, Omnigraffle, the Adobe Suite, Zeplin, etc.</LI>
                    <LI attrLI={{ className: 'border-0' }}>Bonus Considerations </LI>
                </UL>
            </div>
            <div className="job-description">
                <H6>Agency experience</H6>
                <UL>
                    <LI attrLI={{ className: 'border-0' }}>Experience working with Agile development teams</LI>
                    <LI attrLI={{ className: 'border-0' }}>Experience with RITE method usability testing</LI>
                    <LI attrLI={{ className: 'border-0' }}>Experience in visual and motion design; ability to translate UX design into high quality visuals</LI>
                    <LI attrLI={{ className: 'border-0' }}>Mastery of Sketch & InVision</LI>
                    <LI attrLI={{ className: 'border-0' }}>Knowledge of mobile or front-end web programming</LI>
                </UL>
            </div>
            <div className="job-description">
                <H6>Perks</H6>
                <UL>
                    <LI attrLI={{ className: 'border-0' }}>Competitive pay</LI>
                    <LI attrLI={{ className: 'border-0' }}>Competitive medical, dental, and vision insurance plans</LI>
                    <LI attrLI={{ className: 'border-0' }}>-proviCompanyded 401(k) plan</LI>
                    <LI attrLI={{ className: 'border-0' }}>Paid vacation and sick time</LI>
                    <LI attrLI={{ className: 'border-0' }}>Free snacks and beverages</LI>
                </UL>
            </div>
            <div className="job-description">
                <Btn attrBtn={{ className: 'btn me-1', color: 'primary', type: 'button' }}><span><i className="fa fa-check" ></i></span> Save this job</Btn>
                <Btn attrBtn={{ className: 'btn', color: 'primary', type: 'button' }} ><span><i className="fa fa-share-alt"></i></span> Share</Btn>
            </div>
        </Fragment>
    );
};

export default JobDescription;