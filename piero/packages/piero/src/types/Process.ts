type Link = {
    href: string;
    rel: string;
    title: string;
}

type Input = {
    title: string;
    description: string;
    schema: {
        type: string
    };
    minOccurs: number;
    maxOccurs: number;
    options: string[] | null;
}

type Output = {
    title: string;
    description: string;
    schema: {
        type: object,
        format: {
            mediaType: string
        }
    };
};

export type ProcessParams = {
    id: string;
    version: string;
    title: string;
    description: string;
    keywords: string[];
    jobControlOptions: string[];
    outputTransmission: string[];
    inputs: { [param_name: string]: Input };
    outputs: { [output_name: string]: Output };
    links: Link[];
}

export type ProcessBasic = {
    id: string;
    version: string;
    title: string;
    description: string;
    keywords: string[];
    jobControlOptions: string[];
    outputTransmission: string[];
    links: Link[];
}

export type ProcessJob = {
    processID: string;
    title: string;
    type: string;
    jobID: string;
    status: string;
    message: string;
    created: string;
    started: string;
    finished: string;
    updated: string;
    progress: number;
    execution_type: string;
}
