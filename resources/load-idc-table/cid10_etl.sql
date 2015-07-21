
-- CID-10 tables (temporary)

	--DROP TABLE cid10_cat;

	CREATE TABLE cid10_cat (
		cat character(4),
		classif character(1),
		descricao character varying(500),
		descabrev character varying(100),
		refer character(10),
		excluidos character(100),
		extra character(100)
	);


	--DROP TABLE cid10_subcat;

	CREATE TABLE cid10_subcat (
		subcat character(4),
		classif character(1),
		restrsexo character(1),
		causaobito character(1),
		descricao character varying(500),
		descrabrev character varying(100),
		refer character(50),
		excluidos character(100),
		extra character(100)
	);

-- Importing CSV files

	--select * from cid10_cat

	COPY cid10_cat
	FROM '/tmp/CID-10-CATEGORIAS.CSV' 
	DELIMITER ';' 
	CSV 
	HEADER 
	encoding 'ISO-8859-1' ;

	--select * from cid10_subcat

	COPY cid10_subcat
	FROM '/tmp/CID-10-SUBCATEGORIAS.CSV' 
	DELIMITER ';' 
	CSV 
	HEADER 
	encoding 'ISO-8859-1' ;

-- Creating patient_classificationofdiseases
	--select * from patient_classificationofdiseases order by code

	-- Categorias
	insert into patient_classificationofdiseases (code, description, abbreviated_description)
		select cat, descricao, descabrev
		from cid10_cat;

	-- Subcategorias
	insert into patient_classificationofdiseases (code, description, parent_id, abbreviated_description)
		select subcat.subcat, subcat.descricao, cat.id, descrabrev
		from cid10_subcat subcat
		inner join patient_classificationofdiseases cat on cat.code = left(subcat.subcat,3) 
		where cat.parent_id is null and cat.code <> subcat.subcat;

-- Removing temporary tables

	DROP TABLE cid10_cat;
	DROP TABLE cid10_subcat;

