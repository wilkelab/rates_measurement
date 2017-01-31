import numpy as np
from scipy import linalg
import sys

##get_ddg_dict reformats delta-delta Gs from a ddg file. 
##The function outputs a dictionary that uses sites as keys and a list of delta delta Gs as values. 
def get_ddg_dict(ddg_file,site_limit):		
	ddg_dict = {}
	for line in ddg_file:
		line = line.strip()
		
		if line.startswith('SITE'):
			aa_lst = line.split('\t')[1:]
			continue
			
		line_lst = np.fromstring(line,dtype=float,sep=' ')
		site = int(line_lst[0])	
		
		if site_limit == None:
			ddg_lst = np.delete(line_lst,0)
			ddg_dict[site]=ddg_lst
			continue
			
		if site > site_limit:
			break			
		else:
			ddg_lst = np.delete(line_lst,0)
			ddg_dict[site]=ddg_lst
			
	return ddg_dict,aa_lst

def get_codon_s_matrix(ddg_lst,aa_lst):
	temp_s = np.reshape(ddg_lst, (len(ddg_lst), 1))
	aa_s_matrix = temp_s - temp_s.transpose()
	np.fill_diagonal(aa_s_matrix, 0)
	
	aa_to_codon_dict = {'PHE':['TTT','TTC'],
	'LEU':['TTA','TTG','CTT','CTC','CTA','CTG'],
	'ILE':['ATT','ATC','ATA'],
	'MET':['ATG'],
	'VAL':['GTT','GTC','GTA','GTG'],
	'SER':['TCT','TCC','TCA','TCG','AGC','AGT'],
	'PRO':['CCT','CCC','CCA','CCG'],
	'THR':['ACT','ACC','ACA','ACG'],
	'ALA':['GCT','GCC','GCA','GCG'],
	'TYR':['TAT','TAC'],
	'HIS':['CAT','CAC'],
	'GLN':['CAA','CAG'],
	'ASN':['AAT','AAC'],
	'LYS':['AAA','AAG'],
	'ASP':['GAT','GAC'],
	'GLU':['GAA','GAG'],
	'CYS':['TGT','TGC'],
	'TRP':['TGG'],
	'ARG':['CGT','CGC','CGA','CGG','AGA','AGG'],
	'GLY':['GGT','GGC','GGA','GGG']
	}
	
 	codon_s_matrix = np.zeros((1,61))
	for i in range(20):
		codon_s_row=np.array(())
		
		for j in range(20):
			aa=aa_lst[j]
			codon_lst=aa_to_codon_dict[aa]

			aa_s_ij=aa_s_matrix[i,j]
			codon_s_ij_lst=np.repeat(aa_s_ij, len(codon_lst))
			codon_s_row=np.hstack((codon_s_row,codon_s_ij_lst))
		
			for k in range(len(codon_lst)):
				codon_s_matrix=np.append(codon_s_matrix,codon_s_row,axis=0)
	
 	print "Codon s matrix:"
 	print codon_s_matrix
 	#return codon_pi_lst, codon_lst
	
	
##convert a nucleotide mutation rate matrix to a codon mutation rate matrix
def get_codon_mut_rate(nuc_mu_matrix, nuc_lst, codon_lst):
	
	nuc_mu_dict={}
	for i in range(4):
		for j in range(4):
			nuc_mu=nuc_mu_matrix[i,j]
			ni_nj=nuc_lst[i]+nuc_lst[j]
			nuc_mu_dict[ni_nj]=nuc_mu
	
	codon_mu_matrix=np.zeros((61,61))
	for i in range(61):	
		for j in range(61):
			ci = codon_lst[i]
			cj = codon_lst[j]
			pos_diff = [k for k in range(len(ci)) if ci[k] != cj[k]]
			
			if len(pos_diff)==1:
				change_nuc = ci[pos_diff[0]]+cj[pos_diff[0]]
				codon_mu_rate=nuc_mu_dict[change_nuc]
				codon_mu_matrix[i,j]=codon_mu_rate
			else:
				codon_mu_matrix[i,j]=0
	
	#fix the diagonal terms such that each row sums up to 0
	np.fill_diagonal(codon_mu_matrix, -np.nansum(codon_mu_matrix,axis=1))
	
	if np.sum(codon_mu_matrix)-61 > 0.0000001:
		print "Rows in the mutation rate matrix do not add up to 0!"
		sys.exit()
		
	return codon_mu_matrix

##get_q_matrix calculates a substitution matrix Q according to the Mutation-Selection model by Sella and Hirsh.
def get_mutsel_q_matrix(codon_s_matrix,codon_mu_matrix):	

	##FROM PREVIOUS CODE

	q_matrix=s_matrix/(1-np.exp(-s_matrix))
	np.fill_diagonal(q_matrix, 0)
	np.fill_diagonal(q_matrix, -np.nansum(q_matrix,axis=1))
	
	
	print codon_mu_matrix
	q_matrix=np.zeros((61,61))
	for i in range(61):
		for j in range(61):
			if i!=j:
				mu_ij=codon_mu_matrix[i,j]
				mu_ji=codon_mu_matrix[j,i]
				pi_i=codon_pi_lst[i]
				pi_j=codon_pi_lst[j]
				s_ij=np.log( (mu_ji*pi_j)/(mu_ij*pi_i) )
		
				q_ij=mu_ij*( s_ij/(1-np.exp(-s_ij) ))
				q_matrix[i,j]=q_ij
 	
 	np.fill_diagonal(q_matrix, -np.nansum(q_matrix,axis=1))
 	print q_matrix
 	
 	if q_matrix.sum()-0 > 0.0000001:
 		print "Rows in the subsitution matrix do not add up to 0!"
 		sys.exit()
 		
# 	return q_matrix
	
##get_p_matrix calculates a P(t) matrix for a given time with a given Q matrix.
##Here P(t) = e^(tQ) 
def get_p_matrix(t,q_matrix,r=1):
	p_matrix = linalg.expm(r*t*q_matrix)
	if np.sum(p_matrix)-61 > 0.0000001:
		print "Rows in the projection matrix do not add up to 1!"
		sys.exit()
		
	return p_matrix
	
##get_r_tilde calculates a site-wise rate (normalized) using equation ?? from D. K. Sydykova and C. O. Wilke (2017)
def get_r_tilde(site,t,ddg_dict,aa_lst):
		
	##Calculate all sites denominator
	denom_sum = 0	
	for temp_site in ddg_dict:
		ddg_lst = ddg_dict[temp_site]
		pi_lst = get_pi_lst(ddg_lst)
				
		q_matrix = get_mutsel_q_matrix(ddg_lst)
		p_matrix = get_p_matrix(t,q_matrix)
			
		site_sum = 0
		for i in range(20):
			site_sum += pi_lst[i]*p_matrix[i,i]
			
		denom_sum += np.log((20/19.0)*site_sum-(1/19.0))
		
	##Calculate site-wise variables and the numerator
	site_ddg_lst = ddg_dict[site]
 	site_pi_lst = get_pi_lst(site_ddg_lst)
 	site_q_matrix = get_mutsel_q_matrix(site_ddg_lst)
  	site_p_matrix = get_p_matrix(t,site_q_matrix)
	
	site_sum = 0	
  	for i in range(20):
 		site_sum += site_pi_lst[i]*site_p_matrix [i,i]

 	#m is the total number of sites
 	m = len(ddg_dict.keys())
 	r_tilde = np.log( (20/19.0)*site_sum-(1/19.0) ) / ( (1.0/m) * denom_sum)
 	
 	return r_tilde 
 
 	
def main():

	if len(sys.argv) != 4: # wrong number of arguments
		print """Usage:
	python analytically_derived_rates.py <ddG_file> <output_txt_file> <site_limit> 
	"""
		sys.exit()

	infile = sys.argv[1]
	outfile = sys.argv[2]
	site_limit = sys.argv[3]
	
	if site_limit == "all":
		site_limit == None
	else:
		site_limit = int(site_limit)
	
	ddg_file = open(infile,"r")
	out_rate_file = open(outfile,"w")
	out_rate_file.write("site\ttime\tr_tilde\n")
	
	ddg_dict,aa_lst = get_ddg_dict(ddg_file,site_limit)
	
	##Nucleotide mutation matrix
	nuc_lst = ['T','A','C','G']
	a=2
	mu_matrix=np.matrix([[1,1,1,a],[1,1,1,a],[1,1,1,a],[a,a,a,1]])
	
	for site in ddg_dict:
		get_codon_s_matrix(ddg_dict[site],aa_lst)
		#codon_mu_matrix=get_codon_mut_rate(mu_matrix,nuc_lst,codon_lst)
		#get_mutsel_q_matrix(codon_pi_lst,codon_mu_matrix)
	# for site in ddg_dict:				
# 	#	r_tilde_small_t = get_r_tilde_small_t(site,ddg_dict)
# 		#for t in np.arange(0.000002,2,0.02):
# 		t = 0.02
# 		r_tilde_ms = get_r_tilde(site,t,ddg_dict,aa_lst)
# 		line = "%d\t%f\t%.10f\n" %(site,t,r_tilde_ms) 
#  		print line
 		#out_rate_file.write(line)
		
main()