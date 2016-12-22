from math import pow
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--rulefile', help='Name of file that contains the synchronous context-free grammar (left side in CNF, one rule per line)', default='data/rules.binary')
parser.add_argument('-i', '--infile', help='Name of file to be translated (one parse per line)', default='data/episode3-100.zh')
parser.add_argument('-o', '--outfile', help='Name of file to output the translations to', default='translations')
args = parser.parse_args()

def main():
	# get rule probabilities
	rule_file = args.rulefile
	input_file = args.infile
	output_file = args.outfile
	probs, cor_probs, lefts = get_probs(rule_file, 0.1)
	# try and translate based on 
	out = open(output_file, 'w+')
	for line in open(input_file):
		s = line.strip('\n')
		back = cky(cor_probs, lefts, s)	# generate most probable parse tree
		parse = parse2str(probs, back, 0, len(s.split(' ')), 'PHRASE')	# translate based on parse tree
		print(parse)
		out.write(parse)
		out.write('\n')
	out.close()

### Parse rule file into probability dictionary ###
def get_probs(filename, delta):
	lefts = set()
	probs = {}
	cor_probs = {}
	# read rule from each line
	for line in open(filename):
		line = line.strip('\n')
		rule = line.split('\t')
		
		if rule[0] not in probs:
			probs[rule[0]] = {}
		if rule[1] not in probs[rule[0]]:
			probs[rule[0]][rule[1]] = [rule[2], float(rule[3])]
		if float(rule[3]) > probs[rule[0]][rule[1]][1]:
			probs[rule[0]][rule[1]] = [rule[2], float(rule[3])]
		
		# add "identity rules"
		if rule[1].split(' ') == 1 and rule[1] not in probs[rule[0]]:
			probs[rule[0]][rule[1]] = [rule[1], pow(10, -6)]

		if rule[1] not in cor_probs:
			cor_probs[rule[1]] = {}
		if rule[0] not in cor_probs:
			cor_probs[rule[1]][rule[0]] = [ rule[2], 0. ]
		cor_probs[rule[1]][rule[0]][1] += float(rule[3])
		# add "identity rules"
		if rule[1].split(' ') == 1:
			if 'PHRASE' not in cor_probs[rule[1]]:
				cor_probs[rule[1]]['PHRASE'] = [ rule[1], 0. ]
			cor_probs[rule[1]]['PHRASE'][1] += pow(10, -6)

		lefts.add(rule[0])
	
	# add the "glue rule"
	if 'PHRASE' not in probs:
		probs['PHRASE'] = {}
	probs['PHRASE']['PHRASE[0] PHRASE[1]'] = ['PHRASE[0] PHRASE[1]', 1]
	
	if 'PHRASE[0] PHRASE[1]' not in cor_probs:
		cor_probs['PHRASE[0] PHRASE[1]'] = {}
	if 'PHRASE' not in cor_probs['PHRASE[0] PHRASE[1]']:
		cor_probs['PHRASE[0] PHRASE[1]']['PHRASE'] = ['PHRASE[0] PHRASE[1]', 1.]
	
	return probs, cor_probs, lefts

### generates back pointers that represent the parse tree of the sentence ###
def cky(pcfg, lefts, line):
	'''
	inputs: grammar and sentence
	outputs: most probable parse
	'''
	best = {}
	back = {}
	words = line.split(' ')
	n = len(words)+1
	# init all cells of best and back
	for i in range(n-1):
		back[i] = {}
		best[i] = {}
		for j in range(i+1, n):
			back[i][j] = {}
			best[i][j] = {}
			for x in lefts:
				best[i][j][x] = 0
					
	# for unary terminal rules
	for i in range(len(words)):	# going from 0 to n-1 instead of 1 to n like pseudocode
		if words[i] in pcfg:
			for x in pcfg[words[i]]:
				if pcfg[words[i]][x][1] > best[i][i+1][x]:
					best[i][i+1][x] = pcfg[words[i]][x][1]
					back[i][i+1][x] = [x, words[i], i, i+1]

	# for binary nonterminal rules
	for l in range(2, n):
		for i in range(n-l):
			j = i+l
			for k in range(i+1, j):
				for y in back[i][k]:
					Y = y+'[0]'
					for z in back[k][j]:
						Z = z+'[1]'
						yz = Y + ' ' + Z
						if yz in pcfg:
							for X in pcfg[yz]:
								p_prime = pcfg[yz][X][1] * best[i][k][y] * best[k][j][z]
								if p_prime > best[i][j][X]:
									best[i][j][X] = p_prime
									back[i][j][X] = [X, Y, Z, i, k, j]
	return back

### parses through tree of input and generates translation string ###
def parse2str(pcfg, back, i, j, X):
	'''
	Generates string that is the translation of the line based on the back pointers from cky
	'''
	# base case: unary terminal rule
	if X[-3:] == '[0]' or X[-3:] == '[1]':
		X = X[:-3]
	if X not in back[i][j]:
		return ''
	if i+1 == j:
		s = back[i][j][X][1]
		if s not in pcfg[X]:
			if s in pcfg['PHRASE']:
				return pcfg['PHRASE'][s][0]
			return ''
		if pcfg[X][s][0] != '':
			return pcfg[X][s][0] + ' '
		else:
			return ''
	# recurse
	k = back[i][j][X][4]
	Y = back[i][j][X][1]
	Z = back[i][j][X][2]
	s = ''
	for x in pcfg[X][Y+' '+Z][0].split(' '):
		if x == Y:
			s += parse2str(pcfg, back, i, k, Y)
		elif x == Z:
			s += parse2str(pcfg, back, k, j, Z)
		else:
			s += x + ' '
	return s
	
if __name__ == '__main__':
	main()
