import React, { useEffect, useState } from 'react';
import Context from './index';

const ProjectProvider = (props) => {
    const [allData, setAllData] = useState([]);
    const [project, setProject] = useState([]);

    useEffect(() => {
        setAllData([]);
    }, [setAllData, setProject]);

    const addNewProject = (projectData) => {
        const projectTemp = {
            id: allData.length + 1,
            title: projectData.title,
            badge: projectData.badge,
            img: 'user/3.jpg',
            sites: 'Themeforest, australia',
            desc: projectData.desc,
            issue: projectData.issues,
            resolved: projectData.resolved,
            comment: projectData.comment,
            like: '10',
            progress: '70',
            customers_img1: 'user/3.jpg',
            customers_img2: 'user/5.jpg',
            customers_img3: 'user/1.jpg'
        };
        setAllData([...allData, projectTemp]);
    };

    return (
        <Context.Provider
            value={{
                ...props,
                addNewProject: addNewProject,
                project,
                allData,
            }}
        >
            {props.children}
        </Context.Provider>
    );
};

export default ProjectProvider;
